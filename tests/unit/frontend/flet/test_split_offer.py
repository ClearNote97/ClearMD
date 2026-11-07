"""Feature 025 in the flet window: "Split the Large PDFs" in the action bar, left of the page's
secondary button (Back on Review, Convert More on Results), with the presenter's label; hidden
when there is nothing to offer and on the other pages; a press opens Split's step 1 with those
PDFs."""

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest
from support.flet_acceptance import QUIET, Window, click, confirm, converted, pump, windows
from support.gui_fakes import FakeBackend, planned

from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus, PlanWarning
from clearmd.frontend.flet import FletApp
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.state import Tool
from clearmd.i18n import load_catalog

LIMIT = 600.0


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def plan_with_a_large_pdf() -> BatchPlan:
    big = PlanWarning(replace(planned("big.pdf"), cost=2400.0), 2400.0, LIMIT)
    return BatchPlan((big.item,), (), (), (big,))


def to_review(app: FletApp) -> None:
    click(app.home.convert.control)
    app.presenter.add_paths([Path("/docs")])
    click(app.actions.primary)
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION, seconds=30)
    assert app.presenter.page == 2


def beside_the_secondary(app: FletApp) -> bool:
    row = app.actions.control.controls
    return row.index(app.actions.offer) + 1 == row.index(app.actions.secondary)


@pytest.mark.parametrize("language", ["en", "es"])
def test_review_offers_it_left_of_back(flet_window: Window, language: str) -> None:
    backend = FakeBackend(settings=replace(QUIET, language=language), plan=plan_with_a_large_pdf())
    app = flet_window(backend)
    to_review(app)
    catalog = load_catalog(language)
    offer = app.actions.offer
    assert offer.visible and offer.content == catalog.text("gui.offer.split", count=1)
    assert beside_the_secondary(app)
    assert app.actions.secondary.visible and app.actions.secondary.content == catalog.text(
        "gui.plan.back"
    )
    click(app.rail.steps[0])  # another page: the offer belongs to Review
    assert not offer.visible
    click(app.rail.steps[1])
    assert offer.visible
    click(offer)
    assert app.presenter.tool is Tool.SPLIT and app.presenter.page == 1
    assert [row.name for row in app.main.inputs.rows()] == ["big.pdf"]
    assert not offer.visible


def test_review_without_large_pdfs_offers_nothing(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    to_review(app)
    assert not app.actions.offer.visible and app.actions.offer.content == ""


def test_results_offer_it_beside_convert_more(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET, statuses={"a.pdf": OutcomeStatus.STOPPED}))
    to_review(app)
    assert not app.actions.offer.visible  # nothing large in the plan
    confirm(app)
    pump(app, until=lambda: converted(app) and app.presenter.page == 4, seconds=30)
    offer = app.actions.offer
    assert offer.visible and offer.content == "Split the Large PDFs (1)"
    assert beside_the_secondary(app)  # left of Convert More
    click(app.rail.steps[0])  # another page: the bar's offer belongs to Results
    assert not app.actions.offer.visible
    click(app.rail.steps[3])
    assert app.actions.offer.visible
    click(app.actions.offer)
    assert app.presenter.tool is Tool.SPLIT and app.presenter.page == 1
    assert not app.actions.offer.visible


def test_results_without_large_pdfs_offer_nothing(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    to_review(app)
    confirm(app)
    pump(app, until=lambda: converted(app) and app.presenter.page == 4, seconds=30)
    assert not app.actions.offer.visible and app.actions.offer.content == ""
