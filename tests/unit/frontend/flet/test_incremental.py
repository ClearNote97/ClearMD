"""Feature 028 in the flet window: "Replace it if the original changed" as the fourth value of the
setting for existing results, and as Review's third answer, which reaches the presenter as
"changed"."""

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import flet as ft
import pytest
from support.flet_acceptance import QUIET, Window, click, pump, windows
from support.gui_fakes import FakeBackend, planned

from clearmd.backend.schemas.models import BatchPlan
from clearmd.frontend.flet import FletApp
from clearmd.frontend.flet.views.dialogs.settings import SettingsDialog
from clearmd.frontend.presenter import AppState
from clearmd.i18n import load_catalog


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def to_review(app: FletApp) -> None:
    click(app.home.convert.control)
    app.presenter.add_paths([Path("/docs")])
    click(app.actions.primary)
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION, seconds=30)
    app.presenter.go_to(3)  # Convert's page: its primary action is the confirmation


def asking() -> FakeBackend:
    plan = BatchPlan((planned("a.pdf", exists=True),), (), ())
    return FakeBackend(plan=plan, settings=replace(QUIET, on_existing_output="ask"))


@pytest.mark.parametrize("language", ["en", "es"])
def test_review_offers_the_third_answer(flet_window: Window, language: str) -> None:
    backend = asking()
    backend.settings = replace(backend.settings, language=language)
    app = flet_window(backend)
    to_review(app)
    answer = app.review.answer
    assert list(answer.radios) == ["keep", "overwrite", "changed"]
    assert answer.radios["changed"].label == load_catalog(language).text("gui.plan.changed")
    assert app.review.existing.visible and answer.value == "keep"


@pytest.mark.parametrize(
    ("chosen", "sent"), [("keep", False), ("overwrite", True), ("changed", "changed")]
)
def test_each_answer_reaches_the_presenter(
    flet_window: Window, monkeypatch: pytest.MonkeyPatch, chosen: str, sent: bool | str
) -> None:
    app = flet_window(asking())
    to_review(app)
    seen: list[bool | str | None] = []
    monkeypatch.setattr(
        app.presenter, "press_primary", lambda overwrite=None: seen.append(overwrite)
    )
    app.review.answer.choose(chosen)
    app.primary_button.press()
    pump(app, until=lambda: bool(seen), seconds=5)
    assert seen == [sent]


def test_without_the_question_the_setting_decides(flet_window: Window) -> None:
    plan = BatchPlan((planned("a.pdf", exists=True),), (), ())
    app = flet_window(FakeBackend(plan=plan, settings=replace(QUIET, on_existing_output="changed")))
    to_review(app)
    assert not app.review.existing.visible
    assert app.review.overwrite_answer() is None


def test_the_setting_round_trips_changed(flet_window: Window) -> None:
    backend = FakeBackend(settings=QUIET)
    app = flet_window(backend)
    click(app.rail.settings)
    dialog = app.dialogs.current
    assert isinstance(dialog, SettingsDialog)
    control = dialog.controls["on_existing_output"]
    assert isinstance(control, ft.Dropdown)
    catalog = load_catalog("en")
    assert [option.key for option in control.options or []] == [
        "ask",
        "overwrite",
        "skip",
        "changed",
    ]
    assert (control.options or [])[-1].text == catalog.text("gui.settings.existing_changed")
    control.value = "changed"
    dialog.save()
    assert backend.settings.on_existing_output == "changed"
    click(app.rail.settings)
    dialog = app.dialogs.current
    assert isinstance(dialog, SettingsDialog)
    assert dialog.controls["on_existing_output"].value == "changed"
