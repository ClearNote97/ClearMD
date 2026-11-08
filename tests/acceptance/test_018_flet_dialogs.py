"""Feature 018 — Help, welcome and Settings (AC-05); spec/features/018_*/spec.md.

The flet window is built on a page that is not flet's (no screen), on the presenter's fake backend.
"""

import tomllib
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import flet as ft
import pytest
from support.flet_acceptance import (
    QUIET,
    Held,
    Window,
    click,
    confirm,
    converted,
    page_of,
    pump,
    to_review,
    windows,
)
from support.gui_fakes import FakeBackend, MemoryBackend

from clearmd.backend.api import load_settings, settings_path
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.flet import FletApp
from clearmd.frontend.flet.views.dialogs.help import HelpDialog
from clearmd.frontend.flet.views.dialogs.settings import SettingsDialog
from clearmd.frontend.flet.views.dialogs.welcome import WelcomeDialog
from clearmd.frontend.presenter.ports import ApiBackend
from clearmd.i18n import load_catalog


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def escape(app: FletApp) -> None:
    assert app.dialogs.current is not None
    page_of(app).press("Escape")


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_05_help_is_always_one_click_away(
    flet_window: Window, tmp_path: Path, language: str
) -> None:
    held = Held()
    fake = FakeBackend(settings=replace(QUIET, language=language), before_finish=held)
    app = flet_window(fake)
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=held.started.is_set)
    pump(app, seconds=0.1)
    assert not app.rail.help.disabled  # even while converting
    click(app.rail.help)
    dialog = app.dialogs.current
    assert isinstance(dialog, HelpDialog) and dialog.control in page_of(app).dialogs
    shown = " ".join(dialog.texts())
    catalog = load_catalog(language)
    for section in ("how_buttons", "formats", "where", "privacy", "language"):
        assert catalog.text(f"gui.help.{section}") in shown
    assert catalog.text("gui.help.how") not in shown  # flet takes no dropped files (AC-02)
    assert "Settings" in shown and "Ajustes" in shown  # where to switch, in both languages
    assert f"{app.presenter.version}" in shown  # the version is in the help too
    escape(app)  # Esc closes a dialog
    assert app.dialogs.current is None and page_of(app).dialogs == [] and not dialog.control.open
    held.gate.set()
    pump(app, until=lambda: converted(app))


def test_ac_05_the_welcome_appears_until_dont_show_again(flet_window: Window) -> None:
    backend = MemoryBackend(Settings())  # first run: show_welcome is on
    app = flet_window(backend)
    pump(app, until=lambda: app.dialogs.current is not None)
    dialog = app.dialogs.current
    assert isinstance(dialog, WelcomeDialog)
    assert [text for text in dialog.texts() if text[:2] in {"1.", "2.", "3."}] == [
        "1. Choose a tool, then files or a folder",
        "2. Review what will be done",
        "3. Done, your folder opens",
    ]
    dialog.dont_show.value = True
    page_of(app).press("Enter")  # Enter runs the dialog's default action: Start
    assert app.dialogs.current is None and backend.settings.show_welcome is False
    again = flet_window(backend)
    pump(again, seconds=0.1)
    assert again.dialogs.current is None


def test_ac_05_the_welcome_closed_with_esc_asks_again_next_time(flet_window: Window) -> None:
    backend = MemoryBackend(Settings())
    app = flet_window(backend)
    pump(app, until=lambda: app.dialogs.current is not None)
    escape(app)
    assert app.dialogs.current is None and backend.settings.show_welcome is True


def test_ac_05_a_dialog_closed_by_flet_itself_counts_once(flet_window: Window) -> None:
    backend = MemoryBackend(Settings())
    app = flet_window(backend)
    pump(app, until=lambda: app.dialogs.current is not None)
    dialog = app.dialogs.current
    assert isinstance(dialog, WelcomeDialog)
    dialog.dont_show.value = True
    handler = dialog.control.on_dismiss
    assert callable(handler)
    handler()  # type: ignore[call-arg]  # flet calls it with no event when the user dismisses it
    dialog.close_dialog()  # and once more: nothing happens twice
    assert app.dialogs.current is None and backend.settings.show_welcome is False


def test_ac_05_closing_the_window_with_the_welcome_open_keeps_its_answer(
    flet_window: Window,
) -> None:
    backend = MemoryBackend(Settings())
    app = flet_window(backend)
    pump(app, until=lambda: app.dialogs.current is not None)
    assert isinstance(app.dialogs.current, WelcomeDialog)
    app.dialogs.current.dont_show.value = True
    app.close()
    pump(app, until=lambda: app.closing.closed)
    assert backend.settings.show_welcome is False


def test_ac_05_the_settings_window_saves_settings_toml_and_applies_it(flet_window: Window) -> None:
    app = flet_window(ApiBackend())
    pump(app, seconds=0.05)
    if app.dialogs.current is not None:  # the welcome of a first run
        app.dialogs.current.close_dialog()
    app.presenter.go_to(1)  # from Home (feature 023): its primary action shows the language
    click(app.rail.settings)
    dialog = app.dialogs.current
    assert isinstance(dialog, SettingsDialog)
    assert set(dialog.controls) == {
        "language", "theme", "open_output_when_done", "on_existing_output", "recursive",
        "html_strategy", "show_welcome", "summary_format", "images", "merge_into",
    }  # fmt: skip
    language, html = dialog.controls["language"], dialog.controls["html_strategy"]
    assert isinstance(language, ft.Dropdown) and isinstance(html, ft.Dropdown)
    assert [option.text for option in language.options or []] == ["English", "Español"]
    assert dialog.choices["html_strategy"]["article"] == "Only the article"
    language.value, html.value = "es", "article"
    page_of(app).press("Enter")  # Save, the dialog's default action
    written = tomllib.loads(settings_path().read_text(encoding="utf-8"))
    assert written["language"] == "es" and written["html_strategy"] == "article"
    assert load_settings()[0].language == "es"
    assert app.actions.primary.content == "Siguiente"  # applied at once
    click(app.rail.settings)
    restored = app.dialogs.current
    assert isinstance(restored, SettingsDialog)
    restored.restore()
    assert restored.chosen().language == "en"
    escape(app)  # Esc cancels: nothing is saved
    assert load_settings()[0].language == "es" and app.dialogs.current is None


def test_ac_05_settings_are_shut_while_working(flet_window: Window, tmp_path: Path) -> None:
    held = Held()
    app = flet_window(FakeBackend(settings=QUIET, before_finish=held))
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=held.started.is_set)
    pump(app, seconds=0.1)
    assert app.rail.settings.disabled
    app.dialogs.show_settings()  # by any way: it stays shut
    assert app.dialogs.current is None
    held.gate.set()
    pump(app, until=lambda: converted(app))


def test_ac_05_one_dialog_at_a_time_and_keys_go_to_it(flet_window: Window, tmp_path: Path) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    app.presenter.add_paths([tmp_path])
    click(app.rail.help)
    click(app.rail.settings)
    app.dialogs.what_next()
    assert isinstance(app.dialogs.current, HelpDialog) and len(page_of(app).dialogs) == 1
    page_of(app).press("2", ctrl=True)  # the window's keys wait while a dialog is open
    page_of(app).press("Delete")
    assert app.presenter.page == 1 and len(app.main.inputs.rows()) == 1
    page_of(app).press("Enter")  # the help's default: Close
    assert app.dialogs.current is None
