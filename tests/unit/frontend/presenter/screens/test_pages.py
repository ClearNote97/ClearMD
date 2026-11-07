"""Pages and their primary action (feature 007, ADR-0029)."""

from collections.abc import Callable
from pathlib import Path

from support.gui_fakes import FakeBackend, planned
from support.presenter_fakes import FakeView, make, state

from clearmd.backend.schemas.models import (
    BatchPlan,
)
from clearmd.frontend.presenter import AppState, Presenter


def test_every_page_can_be_opened_at_any_time_and_only_the_page_changes() -> None:
    presenter, view, _, _ = make()
    for page in (4, 2, 3, 1):
        presenter.go_to(page)
        assert state(view).page == page
        assert state(view).state is AppState.READY


def test_choose_says_next_and_why_it_is_disabled_without_inputs() -> None:
    presenter, view, _, _ = make()
    presenter.go_to(1)  # from the start screen (feature 023)
    primary = state(view).primary
    assert (primary.label, primary.enabled) == ("Next", False)
    assert primary.hint == "Add at least one file or folder."
    presenter.add_paths([Path("/docs/a.pdf")])
    primary = state(view).primary
    assert primary.enabled and primary.hint == ""


def test_next_plans_and_opens_review_then_next_opens_convert() -> None:
    presenter, view, fake, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    assert state(view).page == 2 and state(view).state is AppState.WAITING_DECISION
    assert state(view).primary.label == "Next"
    presenter.press_primary()
    assert state(view).page == 3 and fake.run_calls == []  # nothing runs before Convert
    assert state(view).primary.label == "Convert" and state(view).primary.enabled


def test_convert_runs_on_its_page_and_results_open_at_the_end() -> None:
    presenter, view, fake, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    presenter.go_to(3)
    presenter.press_primary()
    pages = [value.page for call, value in view.calls if call == "state"]
    view.drain()
    assert 3 in pages and state(view).page == 4
    assert state(view).primary.label == "Open Results Folder"
    assert fake.run_calls


def test_review_and_convert_explain_what_is_missing() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs")])  # chosen, not planned yet
    presenter.go_to(2)
    assert state(view).primary.hint == "Press Next on Choose to see what will happen."
    presenter.go_to(3)
    assert not state(view).primary.enabled
    assert state(view).primary.hint == "Press Next on Choose to see what will happen."
    presenter.go_to(4)
    assert state(view).primary.hint == "Convert something first: the results appear here."


def test_a_plan_with_nothing_to_convert_says_so() -> None:
    plan = BatchPlan((), (), ())
    presenter, view, _, _ = make(FakeBackend(plan=plan))
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    assert not state(view).primary.enabled
    assert state(view).primary.hint == "Nothing here can be converted. Go back to Choose."


def test_changing_the_inputs_after_a_plan_drops_it() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    presenter.go_to(1)
    presenter.add_paths([Path("/more")])
    assert state(view).state is AppState.READY
    presenter.go_to(2)
    assert not state(view).primary.enabled  # press Next on Choose again


def test_nothing_can_be_edited_while_converting() -> None:
    view, fake = FakeView(), FakeBackend()
    waiting: list[Callable[[], None]] = []
    presenter = Presenter(view, fake, detect_theme=lambda: "light", spawn=waiting.append)
    presenter.start()
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    waiting.pop()()
    view.drain()
    presenter.go_to(3)
    presenter.press_primary()
    assert presenter.state is AppState.CONVERTING
    presenter.go_to(1)
    presenter.clear_inputs()
    assert [row.name for row in view.last("inputs")] == ["docs"]
    assert state(view).primary.hint == "Converting… wait for it to finish, or cancel it."


def test_convert_more_keeps_or_clears_the_inputs() -> None:
    plan = BatchPlan((planned("a.pdf"),), (), ())
    for keep, expected in ((True, ["docs"]), (False, [])):
        presenter, view, _, _ = make(FakeBackend(plan=plan))
        presenter.add_paths([Path("/docs")])
        presenter.press_primary()
        view.drain()
        presenter.go_to(3)
        presenter.press_primary()
        view.drain()
        presenter.convert_more(keep=keep)
        assert state(view).page == 1 and state(view).state is AppState.READY
        assert [row.name for row in view.last("inputs")] == expected


def test_the_version_is_known() -> None:
    presenter, _, _, _ = make()
    assert presenter.version[0].isdigit()
