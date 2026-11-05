"""The plan (005, T03; AC-07, AC-08)."""

from pathlib import Path

import pytest
from support.gui_fakes import FakeBackend, planned
from support.presenter_fakes import absolute, make

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.models import (
    BatchPlan,
    SkippedItem,
)
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter import Action, AppState
from clearmd.frontend.presenter.models import RowKind, Stat, Tone


def test_the_plan_is_shown_and_nothing_runs_before_confirming() -> None:
    plan = BatchPlan(
        (planned("a.pdf"), planned("b.pdf", exists=True)),
        (SkippedItem(Path("/docs/notes.md"), SkipReason.ALREADY_MARKDOWN),),
        (),
    )
    presenter, view, fake, _ = make(FakeBackend(plan=plan))
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    shown = view.last("plan")
    assert fake.run_calls == []
    assert shown.summary == "To convert: 2 · Skipped: 1 · Already exist: 1"
    kinds = [row.kind for row in shown.rows]
    assert kinds == [RowKind.CONVERT, RowKind.EXISTS, RowKind.SKIPPED]
    skipped = shown.rows[-1]
    assert skipped.name == "notes.md"
    assert skipped.detail == "already Markdown. It needs no conversion."
    assert shown.asks_about_existing  # the setting is "ask"


def test_the_plan_gives_its_counts_as_figures_for_the_summary_cards() -> None:
    plan = BatchPlan(
        (planned("a.pdf"), planned("b.pdf", exists=True)),
        (SkippedItem(Path("/docs/notes.md"), SkipReason.ALREADY_MARKDOWN),),
        (),
    )
    presenter, view, _, _ = make(FakeBackend(plan=plan))
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert view.last("plan").stats == (
        Stat("To convert", 2, Tone.ACCENT),
        Stat("Skipped", 1, Tone.WARNING),
        Stat("Already exist", 1, Tone.NEUTRAL),
    )


@pytest.mark.parametrize(("setting", "overwrites"), [("overwrite", True), ("skip", False)])
def test_overwrite_and_skip_settings_never_ask(setting: str, overwrites: bool) -> None:
    plan = BatchPlan((planned("b.pdf", exists=True),), (), ())
    presenter, view, fake, _ = make(
        FakeBackend(plan=plan, settings=Settings(on_existing_output=setting))
    )
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert not view.last("plan").asks_about_existing
    presenter.confirm()
    view.drain()
    assert fake.run_calls[-1]["overwrite"](plan.conversions[0]) is overwrites


def test_with_ask_the_users_answer_decides() -> None:
    plan = BatchPlan((planned("b.pdf", exists=True),), (), ())
    presenter, view, fake, _ = make(FakeBackend(plan=plan))
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    presenter.confirm(overwrite=False)
    view.drain()
    assert fake.run_calls[-1]["overwrite"](plan.conversions[0]) is False


def test_a_plan_with_nothing_to_convert_cannot_be_confirmed() -> None:
    plan = BatchPlan((), (SkippedItem(Path("/docs/x.md"), SkipReason.ALREADY_MARKDOWN),), ())
    presenter, view, _, _ = make(FakeBackend(plan=plan))
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert Action.CONFIRM not in view.last("state").enabled
    assert view.last("plan").summary == "To convert: 0 · Skipped: 1 · Already exist: 0"


def test_back_from_the_plan_keeps_the_inputs() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    presenter.back()
    assert view.last("state").state is AppState.READY
    assert [row.path for row in view.last("inputs")] == [absolute("/docs")]
