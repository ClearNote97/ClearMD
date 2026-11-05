"""The work off the UI thread (005, T03; AC-02)."""

import threading
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from support.gui_fakes import FakeBackend
from support.presenter_fakes import make

from clearmd.backend.schemas.models import (
    BatchPlan,
)
from clearmd.frontend.presenter import AppState


def test_the_work_runs_off_the_ui_thread_and_updates_come_back_to_it() -> None:
    presenter, view, fake, _ = make(threaded=True)
    worker_threads: list[int] = []
    real_plan = fake.plan_batch

    def plan_batch(inputs: Sequence[Path], **kwargs: Any) -> BatchPlan:
        worker_threads.append(threading.get_ident())
        return real_plan(inputs, **kwargs)

    fake.plan_batch = plan_batch  # type: ignore[method-assign]
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    for _ in range(200):  # the UI loop
        view.drain()
        if view.last("state").state is AppState.WAITING_DECISION:
            break
        threading.Event().wait(0.01)
    assert view.last("state").state is AppState.WAITING_DECISION
    assert worker_threads and worker_threads[0] != threading.get_ident()
    assert set(view.threads) == {threading.get_ident()}


def test_an_unexpected_error_in_the_work_is_told_and_the_app_goes_on() -> None:
    presenter, view, _, _ = make(FakeBackend(plan_error=RuntimeError("boom")))
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert view.last("state").state is AppState.READY
    assert "Something unexpected went wrong" in view.last("message")
