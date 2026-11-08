"""Feature 016 — Help, welcome and Settings (AC-05); spec/features/016_*/spec.md.

The PySide6 window runs offscreen, on the presenter's fake backend.
"""

import tomllib
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QComboBox, QLabel
from support.gui_fakes import FakeBackend, MemoryBackend
from support.pyside_acceptance import QUIET, Held, confirm, converted, pump, to_review

from clearmd.backend.api import load_settings, settings_path
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter.ports import ApiBackend
from clearmd.frontend.pyside import PySideApp
from clearmd.frontend.pyside.views.dialogs.help import HelpDialog
from clearmd.frontend.pyside.views.dialogs.settings import SettingsDialog
from clearmd.frontend.pyside.views.dialogs.welcome import WelcomeDialog
from clearmd.i18n import load_catalog

Window = Callable[..., PySideApp]


def escape(app: PySideApp) -> None:
    assert app.dialogs.current is not None
    QTest.keyClick(app.dialogs.current, Qt.Key.Key_Escape)
    pump(app, seconds=0.02)


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_05_help_is_always_one_click_away(
    qt_window: Window, tmp_path: Path, language: str
) -> None:
    held = Held()
    fake = FakeBackend(settings=replace(QUIET, language=language), before_finish=held)
    app = qt_window(fake)
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=held.started.is_set)
    pump(app, seconds=0.1)
    assert app.rail.help.isEnabled()  # even while converting
    app.rail.help.click()
    dialog = app.dialogs.current
    assert isinstance(dialog, HelpDialog) and dialog.isVisible()
    shown = " ".join(label.text() for label in dialog.findChildren(QLabel))
    catalog = load_catalog(language)
    for section in ("how", "formats", "where", "privacy", "language"):
        assert catalog.text(f"gui.help.{section}") in shown
    assert "Settings" in shown and "Ajustes" in shown  # where to switch, in both languages
    assert f"{app.presenter.version}" in shown  # the version is in the help too
    escape(app)  # Esc closes a dialog
    assert app.dialogs.current is None and not dialog.isVisible()
    held.gate.set()
    pump(app, until=lambda: converted(app))


def test_ac_05_the_welcome_appears_until_dont_show_again(qt_window: Window) -> None:
    backend = MemoryBackend(Settings())  # first run: show_welcome is on
    app = qt_window(backend)
    pump(app, until=lambda: app.dialogs.current is not None)
    dialog = app.dialogs.current
    assert isinstance(dialog, WelcomeDialog)
    texts = [label.text() for label in dialog.findChildren(QLabel)]
    assert [text for text in texts if text[:2] in {"1.", "2.", "3."}] == [
        "1. Choose a tool, then files or a folder",
        "2. Review what will be done",
        "3. Done, your folder opens",
    ]
    dialog.dont_show.setChecked(True)
    dialog.close_dialog()
    assert backend.settings.show_welcome is False
    again = qt_window(backend)
    pump(again, seconds=0.3)
    assert again.dialogs.current is None


def test_ac_05_the_welcome_closed_with_esc_asks_again_next_time(qt_window: Window) -> None:
    backend = MemoryBackend(Settings())
    app = qt_window(backend)
    pump(app, until=lambda: app.dialogs.current is not None)
    escape(app)
    assert app.dialogs.current is None and backend.settings.show_welcome is True


def test_ac_05_closing_the_window_with_the_welcome_open_keeps_its_answer(
    qt_window: Window,
) -> None:
    backend = MemoryBackend(Settings())
    app = qt_window(backend)
    pump(app, until=lambda: app.dialogs.current is not None)
    assert isinstance(app.dialogs.current, WelcomeDialog)
    app.dialogs.current.dont_show.setChecked(True)
    app.close()
    pump(app, until=lambda: app.closing.closed)
    assert backend.settings.show_welcome is False


def test_ac_05_the_settings_window_saves_settings_toml_and_applies_it(qt_window: Window) -> None:
    app = qt_window(ApiBackend())
    if app.dialogs.current is not None:  # the welcome of a first run
        app.dialogs.current.close_dialog()
    app.presenter.go_to(1)  # past the start screen (023): step 1 has the primary action
    app.rail.settings.click()
    dialog = app.dialogs.current
    assert isinstance(dialog, SettingsDialog)
    assert set(dialog.controls) == {
        "language", "theme", "open_output_when_done", "on_existing_output", "recursive",
        "html_strategy", "show_welcome", "summary_format", "images", "merge_into",
    }  # fmt: skip
    language, html = dialog.controls["language"], dialog.controls["html_strategy"]
    assert isinstance(language, QComboBox) and isinstance(html, QComboBox)
    language.setCurrentText("Español")
    html.setCurrentText("Only the article")
    dialog.save()
    written = tomllib.loads(settings_path().read_text(encoding="utf-8"))
    assert written["language"] == "es" and written["html_strategy"] == "article"
    assert load_settings()[0].language == "es"
    assert app.actions.primary.text() == "Siguiente"  # applied at once
    app.rail.settings.click()
    restored = app.dialogs.current
    assert isinstance(restored, SettingsDialog)
    restored.restore()
    assert restored.chosen().language == "en"
    escape(app)  # Esc cancels: nothing is saved
    assert load_settings()[0].language == "es" and app.dialogs.current is None


def test_ac_05_settings_are_shut_while_working(qt_window: Window, tmp_path: Path) -> None:
    held = Held()
    app = qt_window(FakeBackend(settings=QUIET, before_finish=held))
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=held.started.is_set)
    pump(app, seconds=0.1)
    assert not app.rail.settings.isEnabled()
    held.gate.set()
    pump(app, until=lambda: converted(app))


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_05_settings_show_every_wrapped_line_in_full(qt_window: Window, language: str) -> None:
    app = qt_window(FakeBackend(settings=replace(QUIET, language=language)))
    app.rail.settings.click()
    dialog = app.dialogs.current
    assert isinstance(dialog, SettingsDialog) and dialog.layout() is not None
    pump(app, seconds=0.1)
    assert dialog.height() >= dialog.layout().totalHeightForWidth(dialog.width())  # type: ignore[union-attr]
