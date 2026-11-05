"""Converting (005, T03; AC-09, AC-10)."""

import threading
from pathlib import Path
from typing import Any

import pytest
from support.gui_fakes import FakeBackend, planned
from support.presenter_fakes import converted, make

from clearmd.backend.schemas.models import (
    BatchPlan,
)
from clearmd.frontend.presenter import AppState


def test_progress_says_where_it_is_and_the_time_left_in_plain_words() -> None:
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf")), (), ())
    presenter, view, _, _ = converted(FakeBackend(plan=plan))
    progress = [value for call, value in view.calls if call == "progress"]
    assert progress[0].counter == "1 of 2" and progress[0].name == "a.pdf"
    assert progress[0].icon == "pdf"
    assert progress[0].time_left == "about 2 min left"
    assert progress[1].counter == "2 of 2" and progress[1].fraction == pytest.approx(0.5)


def test_a_file_that_takes_long_shows_a_timer_and_a_reassurance() -> None:
    gate = threading.Event()
    progress_seen: list[Any] = []
    fake = FakeBackend()
    presenter, view, _, clock = make(fake)
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()

    def slow() -> None:  # the file is still converting: the UI loop ticks the timer
        view.drain()
        clock.now += 25
        view.drain(timers=True)
        progress_seen.append(view.last("progress"))
        gate.set()

    fake.before_finish = slow
    presenter.confirm()
    view.drain()
    assert gate.is_set()
    shown = progress_seen[-1]
    assert shown.elapsed == "0:25" and shown.long_file == "Large files can take a few minutes."


def test_cancel_stops_at_once_and_ends_cancelled() -> None:
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf")), (), ())
    fake = FakeBackend(plan=plan)
    presenter, view, _, _ = make(fake)
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    fake.before_finish = presenter.cancel  # pressed while the first file converts
    presenter.confirm()
    view.drain()
    assert fake.run_calls[-1]["cancel"].is_set()
    assert view.last("state").state is AppState.CANCELLED
    assert fake.opened == []  # a cancelled batch never opens the folder by itself


def test_cancel_while_analyzing_discards_the_plan() -> None:
    presenter, view, fake, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    presenter.cancel()
    view.drain()
    assert view.last("state").state is AppState.READY
    assert not [call for call, _ in view.calls if call == "plan"]
