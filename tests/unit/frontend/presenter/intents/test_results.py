"""The result (005, T03; AC-11, AC-12)."""

from pathlib import Path

from support.gui_fakes import FakeBackend, planned
from support.presenter_fakes import converted

from clearmd.backend.schemas.models import (
    BatchPlan,
    OutcomeStatus,
)
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter import Action, AppState
from clearmd.frontend.presenter.models import Stat, Tone


def test_a_clean_batch_finishes_and_opens_the_folder() -> None:
    presenter, view, fake, _ = converted()
    result = view.last("result")
    assert view.last("state").state is AppState.FINISHED
    assert result.counts == "1 converted · 0 skipped · 0 failed"
    assert fake.opened == [Path("/docs/ClearMD_Output")]
    assert Action.OPEN_RESULTS in view.last("state").enabled
    presenter.open_results()
    assert fake.opened == [Path("/docs/ClearMD_Output")] * 2


def test_the_folder_does_not_open_when_the_setting_says_no() -> None:
    _, _, fake, _ = converted(FakeBackend(settings=Settings(open_output_when_done=False)))
    assert fake.opened == []


def test_failures_never_stop_the_batch_and_say_what_to_do() -> None:
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf"), planned("c.pdf")), (), ())
    statuses = {"a.pdf": OutcomeStatus.FAILED, "b.pdf": OutcomeStatus.STOPPED}
    _, view, fake, _ = converted(FakeBackend(plan=plan, statuses=statuses))
    assert len(fake.run_calls) == 1
    result = view.last("result")
    assert view.last("state").state is AppState.FINISHED_WITH_PROBLEMS
    assert result.counts == "1 converted · 0 skipped · 1 failed · 1 stopped"
    details = {row.name: row.detail for row in result.rows}
    assert details["a.pdf"] == "This file is password-protected. Remove the password and try again."
    assert details["b.pdf"].startswith("Exceeded the time limit (10 min).")
    assert result.stats == (
        Stat("Converted", 1, Tone.ACCENT),
        Stat("Skipped", 0, Tone.NEUTRAL),
        Stat("Failed", 1, Tone.DANGER),
        Stat("Stopped", 1, Tone.WARNING),
    )
