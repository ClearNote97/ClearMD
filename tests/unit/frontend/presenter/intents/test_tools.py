"""The tools (feature 023): the start screen, choosing a tool, and Split's choices."""

from dataclasses import replace
from pathlib import Path

from support.gui_fakes import FakeBackend, planned
from support.presenter_fakes import make, state

from clearmd.backend.api import Cut, Keep, SplitSpec
from clearmd.backend.schemas.models import BatchPlan
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.state import HOME, Tool


def test_the_window_opens_on_the_start_screen_with_no_primary_action() -> None:
    _, view, _, _ = make()
    shown = state(view)
    assert shown.page == HOME and shown.tool is Tool.CONVERT
    assert not shown.primary.enabled and shown.primary.label == ""


def test_a_tile_opens_step_1_of_its_tool_and_the_window_speaks_as_it() -> None:
    presenter, view, _, _ = make()
    presenter.choose_tool(Tool.SPLIT)
    shown = state(view)
    assert (shown.page, shown.tool) == (1, Tool.SPLIT)
    assert presenter.catalog.text("gui.page.choose_title") == "Choose What to Split"
    assert view.last("output").tool is Tool.SPLIT
    presenter.choose_tool(Tool.CONVERT)
    assert presenter.catalog.text("gui.page.choose_title") == "Choose What to Convert"


def test_home_comes_back_outside_the_work_and_keeps_the_inputs() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs/a.pdf")])
    assert state(view).page == 1  # dropped on the start screen: step 1
    presenter.go_to(HOME)
    assert state(view).page == HOME and presenter._session.inputs


def test_another_tool_drops_the_plan_made_for_the_first() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert presenter.state is AppState.WAITING_DECISION
    presenter.choose_tool(Tool.SPLIT)
    assert state(view).state is AppState.READY and ("forget", None) in view.calls


def test_split_plans_with_the_cut_and_what_to_keep_from_the_settings() -> None:
    settings = Settings(split_cut="pages", split_pages=30, split_keep="pdf")
    presenter, view, fake, _ = make(FakeBackend(settings=settings))
    presenter.choose_tool(Tool.SPLIT)
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert fake.plan_calls[-1]["split"] == SplitSpec(Cut.PAGES, 30, Keep.PDF)


def test_convert_plans_without_a_split() -> None:
    presenter, view, fake, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert fake.plan_calls[-1]["split"] is None


def test_split_choices_are_remembered_and_drop_the_plan() -> None:
    presenter, view, fake, _ = make()
    presenter.choose_tool(Tool.SPLIT)
    presenter.choose_split(cut="pages", pages=12, keep="markdown")
    assert fake.saved[-1].split_cut == "pages"
    assert (fake.saved[-1].split_pages, fake.saved[-1].split_keep) == (12, "markdown")
    choice = view.last("output")
    assert (choice.split_cut, choice.split_pages, choice.split_keep) == ("pages", 12, "markdown")


def test_split_choices_out_of_bounds_are_refused() -> None:
    presenter, _, fake, _ = make()
    presenter.choose_split(parts=1, pages=0, cut="lines", keep="zip")
    assert fake.saved == []


def test_review_says_how_each_file_will_be_cut() -> None:
    item = replace(planned("a.pdf"), split=SplitSpec(Cut.PARTS, 4))
    backend = FakeBackend(plan=BatchPlan((item,), (), ()))
    presenter, view, _, _ = make(backend)
    presenter.choose_tool(Tool.SPLIT)
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert view.last("plan").rows[0].detail == "✓ Ready to split · PDF · into 4 parts"
