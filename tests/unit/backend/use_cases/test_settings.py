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
    assert defaults.html_strategy == "article"  # the owner's decision on audit v3
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


# --- The remembered output folder (feature 005, ADR-0016/0026) -----------------------------------


def test_the_remembered_output_folder_is_empty_by_default() -> None:
    assert Settings().last_output_folder == ""


@pytest.mark.parametrize(
    "folder",
    [
        "/home/ana/Resultados",
        "C:\\Users\\Ana\\Documents\\Tesis",
        'D:\\Datos "2026"\\salida',
        "/tmp/it's here",
        "C:\\Users\\Ana\\Ñandú y café",
    ],
)
def test_a_remembered_folder_round_trips_whatever_it_holds(folder: str) -> None:
    text = serialize_settings(Settings(last_output_folder=folder))
    assert tomllib.loads(text)["last_output_folder"] == folder
    assert parse_settings(text) == (Settings(last_output_folder=folder), ())


@pytest.mark.parametrize("folder", ["a\x00b", "a\nb", "x" * 5000, 42])
def test_a_remembered_folder_that_is_not_a_plain_path_is_ignored(folder: object) -> None:
    value = f'"{folder}"' if isinstance(folder, str) else str(folder)
    settings, warnings = parse_settings(
        f"last_output_folder = {value}\n".replace("\x00", "\\u0000")
    )
    assert settings.last_output_folder == ""
    assert [w.problem for w in warnings] in (
        [SettingsProblem.INVALID_VALUE],
        [SettingsProblem.UNREADABLE],
    )


def test_saving_refuses_a_value_reading_would_refuse() -> None:
    with pytest.raises(ValueError):
        serialize_settings(Settings(language="fr"))


@pytest.mark.parametrize(
    "folder", ["/tmp/a\nb", "/tmp/\udcff", "/" + "x" * 5000], ids=["newline", "surrogate", "long"]
)
def test_a_path_that_cannot_be_stored_is_refused_before_writing(folder: str) -> None:
    from clearmd.backend.schemas.settings import valid_path_setting

    assert not valid_path_setting(folder)
    with pytest.raises(ValueError):
        serialize_settings(Settings(last_output_folder=folder))
