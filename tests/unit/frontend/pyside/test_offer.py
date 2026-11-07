"""Feature 025 in the Qt window: "Split the Large PDFs (N)" on Review and Results, in the action
bar next to the secondary action; hidden when there is nothing to offer (AC-04)."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Qt
from support.gui_fakes import FakeBackend, planned
from support.pyside_acceptance import QUIET, pump

from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus, PlanWarning
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.pyside import PySideApp

Window = Callable[..., PySideApp]


def plan_with_large() -> BatchPlan:
    """One PDF over the time limit: the presenter offers to split it."""
    big = PlanWarning(replace(planned("big.pdf"), cost=2400.0), 2400.0, 600.0)
    return BatchPlan((big.item,), (), (), (big,))


def to_review(app: PySideApp, folder: Path) -> None:
    app.presenter.choose_tool(Tool.CONVERT)
    app.presenter.add_paths([folder])
    app.presenter.analyze()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    pump(app, seconds=0.05)


def test_review_offers_it_with_its_label_and_the_press_opens_split(
    window: Window, tmp_path: Path
) -> None:
    app = window(FakeBackend(settings=QUIET, plan=plan_with_large()))
    assert app.actions.offer.isHidden()  # nothing to offer on Home
    to_review(app, tmp_path)
    assert app.presenter.page == 2
    offer = app.actions.offer
    assert not offer.isHidden() and offer.text() == "Split the Large PDFs (1)"
    assert offer.focusPolicy() is not Qt.FocusPolicy.NoFocus  # reachable by Tab
    app.presenter.go_to(1)
    assert offer.isHidden()  # Review's own, not step 1's
    app.presenter.go_to(2)
    assert not offer.isHidden()
    offer.click()
    assert app.presenter.tool is Tool.SPLIT and app.presenter.page == 1
    assert offer.isHidden()


def test_no_offer_without_large_pdfs(window: Window, tmp_path: Path) -> None:
    app = window()
    to_review(app, tmp_path)
    assert app.presenter.page == 2 and app.actions.offer.isHidden()


def test_results_offer_it_for_a_pdf_stopped_at_a_limit(window: Window, tmp_path: Path) -> None:
    app = window(FakeBackend(settings=QUIET, statuses={"a.pdf": OutcomeStatus.STOPPED}))
    to_review(app, tmp_path)
    assert app.actions.offer.isHidden()
    app.presenter.confirm()
    pump(app, until=lambda: app.presenter.page == 4, seconds=10)
    offer = app.actions.offer
    assert not offer.isHidden() and offer.text() == "Split the Large PDFs (1)"
    assert not app.actions.secondary.isHidden()  # beside Convert More
    offer.click()
    assert app.presenter.tool is Tool.SPLIT and app.presenter.page == 1


def test_the_offer_speaks_spanish(window: Window, tmp_path: Path) -> None:
    app = window(FakeBackend(settings=replace(QUIET, language="es"), plan=plan_with_large()))
    to_review(app, tmp_path)
    assert app.actions.offer.text() == "Dividir los PDF Muy Grandes (1)"
