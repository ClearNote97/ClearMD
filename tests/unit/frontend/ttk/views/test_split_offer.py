"""Split the Large PDFs from Convert (feature 025, AC-04): in the action bar, just left of Back on
Review and of Convert More on Results; hidden when nothing is offered; the press runs
presenter.split_large."""

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from support.gui_close import shut
from support.gui_fakes import FakeBackend, planned
from support.ttk_unit import confirm, pump

from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus, PlanWarning
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.ttk import TtkApp

QUIET = Settings(show_welcome=False, theme="light")


def large_plan() -> BatchPlan:
    big = PlanWarning(replace(planned("big.pdf"), cost=2400.0), 2400.0, 600.0)
    return BatchPlan((big.item, planned("small.docx")), (), (), (big,))


def opened(fake: FakeBackend) -> TtkApp:
    fake.settings = QUIET
    app = TtkApp(fake)
    app.start()
    pump(app, seconds=0.1)
    return app


def reviewed(app: TtkApp) -> None:
    app.presenter.add_paths([Path("/docs")])
    app.presenter.analyze()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)


def test_review_shows_the_offer_left_of_back_and_the_press_splits(display: str) -> None:
    app = opened(FakeBackend(plan=large_plan()))
    try:
        reviewed(app)
        offer, back = app.actions.offer, app.actions.secondary
        assert offer.winfo_ismapped() and offer.cget("text") == "Split the Large PDFs (1)"
        assert offer.cget("takefocus") != 0  # reachable with Tab
        assert back.winfo_ismapped() and back.cget("text") == "Back"
        assert offer.winfo_rootx() < back.winfo_rootx()  # just left of the secondary action
        offer.invoke()
        pump(app, seconds=0.05)
        assert (app.presenter.page, app.presenter.tool) == (1, Tool.SPLIT)
        assert app.main.inputs.names() == ["big.pdf"]
        assert not offer.winfo_manager()  # step 1 has no offer
    finally:
        shut(app)


def test_review_hides_it_when_nothing_is_offered(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path])
    app.presenter.analyze()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    assert app.last_plan is not None and app.last_plan.split_offer == ""
    assert not app.actions.offer.winfo_manager()


def test_results_show_it_next_to_convert_more(
    display: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = opened(FakeBackend(statuses={"a.pdf": OutcomeStatus.STOPPED}))
    try:
        reviewed(app)
        confirm(app)
        pump(app, until=lambda: app.presenter.page == 4)
        offer = app.actions.offer
        assert offer.winfo_ismapped() and offer.cget("text") == "Split the Large PDFs (1)"
        convert_more = app.actions.secondary
        assert convert_more.winfo_ismapped()
        assert offer.winfo_rootx() < convert_more.winfo_rootx()  # in the secondary actions' row
        seen: list[Any] = []
        monkeypatch.setattr(app.presenter, "split_large", lambda: seen.append(1))
        offer.invoke()
        assert seen == [1]
        app.presenter.go_to(2)  # on another page the bar has no offer
        pump(app, seconds=0.05)
        assert not offer.winfo_manager()
    finally:
        shut(app)


def test_results_hide_it_when_nothing_is_offered(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path])
    app.presenter.analyze()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    confirm(app)
    pump(app, until=lambda: app.presenter.page == 4)
    assert app.last_result is not None and app.last_result.split_offer == ""
    assert not app.actions.offer.winfo_manager()
