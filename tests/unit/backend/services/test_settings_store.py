from pathlib import Path

import pytest

from clearmd.backend.schemas.settings import Settings, SettingsProblem
from clearmd.backend.services.settings_store import load_settings, settings_path


def test_the_settings_file_lives_in_the_user_config_folder(tmp_path: Path) -> None:
    # tests/conftest.py points XDG_CONFIG_HOME at a temporary folder for every test.
    assert settings_path().parts[-2:] == ("ClearMD", "settings.toml")


def test_a_missing_file_means_defaults_without_warnings() -> None:
    assert load_settings() == (Settings(), ())


def test_the_file_is_read(tmp_path: Path) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True)
    path.write_text('language = "es"\n', encoding="utf-8")
    settings, warnings = load_settings()
    assert settings.language == "es"
    assert warnings == ()


def test_an_unreadable_file_means_defaults_and_a_warning() -> None:
    path = settings_path()
    path.parent.mkdir(parents=True)
    path.write_text('language = "es"\n', encoding="utf-8")
    path.chmod(0)
    try:
        settings, warnings = load_settings()
    finally:
        path.chmod(0o644)
    assert settings == Settings()
    assert [w.problem for w in warnings] == [SettingsProblem.UNREADABLE]


def test_a_non_utf8_file_means_defaults_and_a_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True)
    path.write_bytes(b'language = "\xff"\n')
    settings, warnings = load_settings()
    assert settings == Settings()
    assert [w.problem for w in warnings] == [SettingsProblem.UNREADABLE]


# --- Writing (feature 005, ADR-0026) -------------------------------------------------------------


def test_saved_settings_are_read_back() -> None:
    from clearmd.backend.services.settings_store import save_settings

    chosen = Settings(language="es", theme="dark", last_output_folder="/home/ana/Resultados")
    save_settings(chosen)
    assert load_settings() == (chosen, ())


def test_saving_is_atomic_and_leaves_no_temporary_file(monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    from clearmd.backend.services.settings_store import save_settings

    save_settings(Settings(language="es"))
    before = settings_path().read_text(encoding="utf-8")

    def broken_replace(source: object, target: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", broken_replace)
    with pytest.raises(OSError):
        save_settings(Settings(language="en", theme="dark"))
    # The old file is intact, and the half-written one is gone.
    assert settings_path().read_text(encoding="utf-8") == before
    assert sorted(p.name for p in settings_path().parent.iterdir()) == ["settings.toml"]


def test_saving_creates_the_folder() -> None:
    from clearmd.backend.services.settings_store import save_settings

    assert not settings_path().parent.exists()
    save_settings(Settings())
    assert settings_path().is_file()
