"""Language, settings, welcome (005, T03; AC-03, AC-14 to AC-16)."""

from dataclasses import replace
from pathlib import Path

from support.gui_fakes import FakeBackend
from support.presenter_fakes import make

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.models import (
    BatchPlan,
    SkippedItem,
)
from clearmd.backend.schemas.settings import Settings, SettingsProblem, SettingsWarning
from clearmd.i18n import load_catalog


def test_texts_follow_the_language_setting() -> None:
    plan = BatchPlan((), (SkippedItem(Path("/docs/x.md"), SkipReason.ALREADY_MARKDOWN),), ())
    presenter, view, _, _ = make(FakeBackend(plan=plan, settings=Settings(language="es")))
    assert view.last("state").label == "Listo"
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert view.last("plan").rows[0].detail == "Omitido: ya es Markdown. No necesita conversión."


def test_saving_settings_applies_the_language_and_the_theme() -> None:
    presenter, view, fake, _ = make(theme="dark")
    assert view.last("theme") == "dark"  # "system" follows the system
    presenter.save_settings(replace(fake.settings, language="es", theme="light"))
    assert fake.saved[-1].language == "es"
    assert view.last("language") == "es" and view.last("theme") == "light"
    assert view.last("state").label == "Listo"


def test_a_settings_file_that_cannot_be_written_is_told() -> None:
    presenter, view, fake, _ = make(FakeBackend(save_error=PermissionError("read-only")))
    presenter.save_settings(replace(fake.settings, theme="dark"))
    assert (
        view.last("message")
        == "ClearMD could not save the settings. Your changes apply until you close it."
    )


def test_restore_defaults_saves_the_defaults() -> None:
    presenter, _, fake, _ = make(FakeBackend(settings=Settings(language="es", recursive=False)))
    presenter.restore_defaults()
    assert fake.saved[-1] == Settings()


def test_the_welcome_shows_once_until_dismissed() -> None:
    _, view, fake, _ = make()
    steps = view.last("welcome")
    english = load_catalog("en")
    assert steps == tuple(english.text(f"gui.welcome.step{n}") for n in (1, 2, 3))
    presenter, _, _, _ = make(fake)
    presenter.dismiss_welcome(show_again=False)
    assert fake.saved[-1].show_welcome is False
    _, again, _, _ = make(FakeBackend(settings=fake.settings))
    assert not [call for call, _ in again.calls if call == "welcome"]


def test_settings_problems_at_start_are_told_in_plain_words() -> None:
    warnings = (SettingsWarning("colour", SettingsProblem.UNKNOWN_KEY),)
    _, view, _, _ = make(FakeBackend(warnings=warnings))
    assert "colour" in view.last("message")


def test_rows_carry_their_file_icon_and_the_state_its_step(tmp_path: Path) -> None:
    (tmp_path / "a.pdf").write_bytes(b"%PDF")
    presenter, view, _, _ = make()
    assert view.last("state").step == 1
    presenter.add_paths([tmp_path / "a.pdf", tmp_path])
    assert [row.icon for row in view.last("inputs")] == ["pdf", "folder"]
    presenter.analyze()
    view.drain()
    assert view.last("state").step == 2
    assert all(row.icon for row in view.last("plan").rows)
    presenter.confirm()
    view.drain()
    assert view.last("state").step == 4
