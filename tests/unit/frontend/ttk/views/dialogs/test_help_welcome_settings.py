"""Help, welcome and settings through the window (005, T06)."""

from support.gui_close import shut
from support.gui_fakes import FakeBackend
from support.ttk_unit import pump

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.views import dialogs

# --- Help, welcome, settings (T06) ---------------------------------------------------------------


def test_help_opens_from_the_rail_and_esc_closes_it(app: TtkApp) -> None:
    app.rail.help.invoke()
    pump(app, seconds=0.2)
    assert app.dialog is not None
    assert app.dialog.title() == "How to use ClearMD"
    texts = [child.cget("text") for child in app.dialog.body.winfo_children()]
    assert "Your privacy" in texts and "What it converts" in texts
    app.dialog.focus_force()
    pump(app, seconds=0.1)
    app.dialog.event_generate("<Escape>", when="tail")
    pump(app, until=lambda: app.dialog is None, seconds=1.0)
    assert app.dialog is None


def test_the_welcome_appears_once_and_can_be_dismissed_for_good(display: str) -> None:
    fake = FakeBackend(settings=Settings(show_welcome=True))
    app = TtkApp(fake)
    try:
        app.start()
        pump(app, until=lambda: app.dialog is not None)
        assert isinstance(app.dialog, dialogs.welcome.WelcomeDialog)
        app.dialog.dont_show.set(True)
        app.dialog.close()
        assert app.dialog is None
        assert fake.saved[-1].show_welcome is False
    finally:
        shut(app)


def test_settings_save_applies_the_language_and_theme(app: TtkApp) -> None:
    app.rail.settings.invoke()
    pump(app, seconds=0.2)
    dialog = app.dialog
    assert isinstance(dialog, dialogs.settings.SettingsDialog)
    assert set(dialog.values) == {
        "language", "theme", "open_output_when_done", "on_existing_output", "recursive",
        "html_strategy", "show_welcome", "summary_format", "images",
    }  # fmt: skip
    dialog.values["language"].set("Español")
    dialog.values["theme"].set("Dark")
    dialog.values["recursive"].set(False)
    dialog.save()
    pump(app, seconds=0.2)
    assert app.dialog is None
    assert app.presenter.settings.language == "es" and not app.presenter.settings.recursive
    assert app.style.theme_use() == "clearmd-dark"
    assert app.actions.primary.cget("text") == "Siguiente"


def test_restore_defaults_resets_the_controls_until_saved(app: TtkApp) -> None:
    app.presenter.save_settings(Settings(language="es", show_welcome=False, recursive=False))
    app.rail.settings.invoke()
    pump(app, seconds=0.2)
    dialog = app.dialog
    assert isinstance(dialog, dialogs.settings.SettingsDialog)
    dialog.restore()
    assert dialog.chosen() == Settings()
    dialog.close()
    assert app.presenter.settings.language == "es"  # nothing saved without Save
