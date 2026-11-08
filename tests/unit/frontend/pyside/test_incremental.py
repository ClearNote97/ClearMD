"""Feature 028 in the Qt window: "Replace it if the original changed" in Settings, and Review's
third answer about existing results, sent to the presenter as "changed" (AC-04)."""

from collections.abc import Callable
from pathlib import Path

import pytest
from PySide6.QtWidgets import QComboBox
from support.gui_fakes import FakeBackend, planned
from support.pyside_acceptance import QUIET, pump

from clearmd.backend.api import changed_since_result
from clearmd.backend.schemas.models import BatchPlan
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.pyside import PySideApp
from clearmd.frontend.pyside.views.dialogs.settings import SettingsDialog

Window = Callable[..., PySideApp]


def test_the_setting_has_the_fourth_choice_and_round_trips(window: Window) -> None:
    backend = FakeBackend(settings=QUIET)
    app = window(backend)
    app.rail.settings.click()
    dialog = app.dialogs.current
    assert isinstance(dialog, SettingsDialog)
    combo = dialog.controls["on_existing_output"]
    assert isinstance(combo, QComboBox)
    items = [combo.itemText(index) for index in range(combo.count())]
    assert items[-1] == "Replace it if the original changed" and len(items) == 4
    combo.setCurrentText("Replace it if the original changed")
    dialog.save()
    assert backend.saved[-1].on_existing_output == "changed"
    app.rail.settings.click()
    again = app.dialogs.current
    assert isinstance(again, SettingsDialog) and again.chosen().on_existing_output == "changed"
    again.close_dialog()


def to_review_with_an_existing_result(app: PySideApp, folder: Path) -> None:
    app.presenter.choose_tool(Tool.CONVERT)
    app.presenter.add_paths([folder])
    app.presenter.analyze()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)


def backend_with_existing() -> FakeBackend:
    return FakeBackend(settings=QUIET, plan=BatchPlan((planned("a.pdf", exists=True),), (), ()))


@pytest.mark.parametrize(
    ("answer", "sent"), [("keep", False), ("overwrite", True), ("changed", "changed")]
)
def test_reviews_three_answers_reach_the_presenter(
    window: Window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, answer: str, sent: object
) -> None:
    app = window(backend_with_existing())
    to_review_with_an_existing_result(app, tmp_path)
    review = app.review
    assert review.existing.isVisible() and review.changed.text() == "Only if the original changed"
    getattr(review, answer).click()
    pressed: list[object] = []
    monkeypatch.setattr(app.presenter, "press_primary", pressed.append)
    monkeypatch.setattr("clearmd.frontend.presenter.chrome.primary_gate.gate_open", lambda *_: True)
    app.primary_button.press()
    assert pressed == [sent]


def test_changed_runs_the_batch_with_the_changed_rule(window: Window, tmp_path: Path) -> None:
    backend = backend_with_existing()
    app = window(backend)
    to_review_with_an_existing_result(app, tmp_path)
    app.review.changed.click()
    app.presenter.go_to(3)
    app.presenter.confirm(app.review.overwrite_answer())
    pump(app, until=lambda: bool(backend.run_calls), seconds=5)
    pump(app, until=lambda: app.presenter.page == 4, seconds=5)
    assert backend.run_calls[-1]["overwrite"] is changed_since_result


def test_nothing_asked_no_answer(window: Window, tmp_path: Path) -> None:
    app = window()
    to_review_with_an_existing_result(app, tmp_path)
    assert not app.review.existing.isVisible() and app.review.overwrite_answer() is None
