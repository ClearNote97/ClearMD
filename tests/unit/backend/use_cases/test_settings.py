"""Reading and writing settings.toml never crashes (ADR-0012, ADR-0017, AC-33)."""

import tomllib

import pytest

from clearmd.backend.schemas.settings import Settings, SettingsProblem
from clearmd.backend.use_cases.settings import parse_settings, serialize_settings


def test_an_empty_file_means_every_default() -> None:
    settings, warnings = parse_settings("")
    assert settings == Settings()
    assert warnings == ()


def test_the_defaults_follow_adr_0012_and_0017() -> None:
    defaults = Settings()
    assert defaults.language == "en"
    assert defaults.theme == "system"
    assert defaults.open_output_when_done is True
    assert defaults.on_existing_output == "ask"
    assert defaults.recursive is True
    assert defaults.html_strategy == "full"
    assert defaults.show_welcome is True


def test_valid_values_are_read() -> None:
    settings, warnings = parse_settings(
        'language = "es"\non_existing_output = "skip"\nrecursive = false\ntheme = "dark"\n'
    )
    assert (settings.language, settings.on_existing_output, settings.recursive, settings.theme) == (
        "es",
        "skip",
        False,
        "dark",
    )
    assert warnings == ()


@pytest.mark.parametrize(
    ("line", "key"),
    [
        ('language = "fr"', "language"),
        ('recursive = "yes"', "recursive"),
        ("on_existing_output = 3", "on_existing_output"),
        ('theme = ["dark"]', "theme"),
    ],
)
def test_an_invalid_value_falls_back_to_its_default_with_a_warning(line: str, key: str) -> None:
    settings, warnings = parse_settings(line + "\n")
    assert getattr(settings, key) == getattr(Settings(), key)
    assert [(w.key, w.problem) for w in warnings] == [(key, SettingsProblem.INVALID_VALUE)]


def test_an_unknown_key_is_ignored_with_a_warning() -> None:
    settings, warnings = parse_settings('colour = "blue"\nlanguage = "es"\n')
    assert settings.language == "es"
    assert [(w.key, w.problem) for w in warnings] == [("colour", SettingsProblem.UNKNOWN_KEY)]


def test_a_broken_file_means_defaults_and_one_warning() -> None:
    settings, warnings = parse_settings('language = "es\nrecursive = \n')
    assert settings == Settings()
    assert [w.problem for w in warnings] == [SettingsProblem.UNREADABLE]


def test_serialization_round_trips_and_is_valid_toml() -> None:
    custom = Settings(language="es", on_existing_output="overwrite", recursive=False)
    text = serialize_settings(custom)
    assert tomllib.loads(text)["language"] == "es"
    assert parse_settings(text) == (custom, ())
