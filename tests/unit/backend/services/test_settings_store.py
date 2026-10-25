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
