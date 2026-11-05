"""Feature 005 — Help, welcome and settings (AC-13 to AC-15); spec/features/005_*/spec.md.

The window runs under a display (a virtual one when there is none), mostly on a fake backend.
"""

import tomllib
from collections.abc import Callable
from pathlib import Path

import pytest
from support.gui_fakes import FakeBackend, MemoryBackend
from support.ttk_acceptance import (
    QUIET,
    Held,
    confirm,
    converted,
    pump,
    replace_settings,
    to_review,
)

from clearmd.backend.api import load_settings, settings_path
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter.ports import ApiBackend
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.views import dialogs
from clearmd.i18n import load_catalog


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_13_help_is_always_one_click_away(
    window: Callable[..., TtkApp], tmp_path: Path, language: str
) -> None:
    held = Held()
    fake = FakeBackend(settings=replace_settings(QUIET, language=language), before_finish=held)
    app = window(fake)
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=held.started.is_set)
    pump(app, seconds=0.1)
    assert app.rail.help.instate(["!disabled"])  # even while converting
    app.rail.help.invoke()
    assert app.dialog is not None
    shown = " ".join(str(child.cget("text")) for child in app.dialog.body.winfo_children())
    catalog = load_catalog(language)
    for section in ("how", "formats", "where", "privacy", "language"):
        assert catalog.text(f"gui.help.{section}") in shown
    assert "Settings" in shown and "Ajustes" in shown  # where to switch, in both languages
    app.dialog.close()
    held.gate.set()
    pump(app, until=lambda: converted(app))


def test_ac_14_the_welcome_appears_until_dont_show_again(
    window: Callable[..., TtkApp],
) -> None:
    backend = MemoryBackend(Settings())  # first run: show_welcome is on
    app = window(backend)
    pump(app, until=lambda: app.dialog is not None)
    dialog = app.dialog
    assert isinstance(dialog, dialogs.welcome.WelcomeDialog)
    texts = [str(child.cget("text")) for child in dialog.body.winfo_children()]
    assert [text for text in texts if text[:2] in {"1.", "2.", "3."}] == [
        "1. Choose files or a folder",
        "2. Review what will be converted",
        "3. Done, your folder opens",
    ]
    dialog.dont_show.set(True)
    dialog.close()
    assert backend.settings.show_welcome is False
    again = window(backend)
    pump(again, seconds=0.3)
    assert again.dialog is None


def test_ac_15_the_settings_window_saves_settings_toml_and_applies_it(
    window: Callable[..., TtkApp],
) -> None:
    app = window(ApiBackend())
    if app.dialog is not None:  # the welcome of a first run
        app.dialog.close()
    app.rail.settings.invoke()
    dialog = app.dialog
    assert isinstance(dialog, dialogs.settings.SettingsDialog)
    assert set(dialog.values) == {
        "language", "theme", "open_output_when_done", "on_existing_output", "recursive",
        "html_strategy", "show_welcome", "summary_format", "images",  # the last one: feature 009
    }  # fmt: skip
    dialog.values["language"].set("Español")
    dialog.values["html_strategy"].set("Only the article")
    dialog.save()
    written = tomllib.loads(settings_path().read_text(encoding="utf-8"))
    assert written["language"] == "es" and written["html_strategy"] == "article"
    assert load_settings()[0].language == "es"
    assert app.actions.primary.cget("text") == "Siguiente"  # applied at once
    app.rail.settings.invoke()
    restored = app.dialog
    assert isinstance(restored, dialogs.settings.SettingsDialog)
    restored.restore()
    assert restored.chosen().language == "en"
