"""Feature 018 — Closing the window, while converting or not (AC-07); spec/features/018_*/spec.md.

The flet window is built on a page that is not flet's (no screen), on the presenter's fake backend.
"""

import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from support.flet_acceptance import (
    QUIET,
    Held,
    Window,
    click,
    confirm,
    page_of,
    pump,
    to_review,
    windows,
)
from support.gui_fakes import FakeBackend

from clearmd.backend.schemas.models import BatchPlan
from clearmd.frontend.flet.views.dialogs.close_question import CloseQuestionDialog
from clearmd.frontend.presenter import AppState


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def test_ac_07_closing_while_converting_cancels_and_waits_for_the_summary(
    flet_window: Window, tmp_path: Path
) -> None:
    marker = tmp_path / "Resumen_ClearMD.md"
    cancelled: list[bool] = []

    class Slow(FakeBackend):
        def run_batch(self, plan: BatchPlan, **kwargs: Any) -> Any:
            kwargs["cancel"]._event.wait(5)  # converting until cancelled  # noqa: SLF001
            time.sleep(0.3)  # the current file stops, then the summary is written
            marker.write_text("summary", encoding="utf-8")
            cancelled.append(kwargs["cancel"].is_set())
            return super().run_batch(plan, **kwargs)

    app = flet_window(Slow(settings=QUIET))
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=lambda: app.presenter.state is AppState.CONVERTING)
    page = page_of(app)
    page.close_button()  # the window's own close button: it asks first (038)
    question = app.dialogs.current
    assert isinstance(question, CloseQuestionDialog) and not page.hidden
    click(question.close)  # Close: cancel, hide, wait for the batch
    assert page.hidden and not page.destroyed and not app.closing.closed  # waiting for the batch
    pump(app, until=lambda: app.closing.closed, seconds=15)
    assert app.closing.closed and page.destroyed and marker.is_file() and cancelled == [True]


@pytest.mark.parametrize("analyzing", [False, True])
def test_ac_07_closing_otherwise_closes_at_once(
    flet_window: Window, tmp_path: Path, analyzing: bool
) -> None:
    held = Held()

    class SlowPlan(FakeBackend):
        def plan_batch(self, inputs: Any, **kwargs: Any) -> BatchPlan:
            held()
            return super().plan_batch(inputs, **kwargs)

    app = flet_window(SlowPlan(settings=QUIET))
    page = page_of(app)
    try:
        if analyzing:  # an analysis is dropped: nothing to wait for
            app.presenter.add_paths([tmp_path])
            click(app.actions.primary)
            pump(app, until=held.started.is_set)
            assert app.presenter.state is AppState.ANALYZING
        page.close_button()
        assert app.closing.closed and page.destroyed and not page.hidden
        app.after(0, lambda: pytest.fail("nothing runs once the window is gone"))
        pump(app, seconds=0.05)
    finally:
        held.gate.set()
