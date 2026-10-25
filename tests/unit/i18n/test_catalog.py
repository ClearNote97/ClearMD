import string
import tomllib
from importlib import resources

import pytest

from clearmd.backend.schemas.errors import ErrorCode, SkipReason
from clearmd.i18n import SUPPORTED_LANGUAGES, Catalog, flatten, load_catalog, resolve_language


def _raw(language: str) -> dict[str, str]:
    data = tomllib.loads(
        resources.files("clearmd.i18n").joinpath(f"{language}.toml").read_text("utf-8")
    )
    return flatten(data)


def _placeholders(text: str) -> set[str]:
    return {field for _, field, _, _ in string.Formatter().parse(text) if field}


def test_both_catalogs_have_the_same_keys() -> None:
    assert set(_raw("en")) == set(_raw("es"))


@pytest.mark.parametrize("key", sorted(_raw("en")))
def test_both_catalogs_use_the_same_placeholders(key: str) -> None:
    assert _placeholders(_raw("en")[key]) == _placeholders(_raw("es")[key])


@pytest.mark.parametrize("language", SUPPORTED_LANGUAGES)
def test_every_error_code_and_skip_reason_has_its_texts(language: str) -> None:
    keys = set(_raw(language))
    for code in ErrorCode:
        assert {code.message_key, code.action_key} <= keys
    for reason in SkipReason:
        assert reason.key in keys


def test_password_message_matches_ac_22() -> None:
    catalog = load_catalog("en")
    code = ErrorCode.PASSWORD_PROTECTED
    assert catalog.error(code) == (
        "This PDF is password-protected. Remove the password and try again."
    )


def test_texts_are_formatted_with_named_values() -> None:
    catalog = Catalog("en", {"greeting": "Hello, {name}!"})
    assert catalog.text("greeting", name="Ana") == "Hello, Ana!"


def test_unknown_key_is_a_programming_error() -> None:
    with pytest.raises(KeyError):
        Catalog("en", {}).text("missing.key")


def test_unknown_language_cannot_be_loaded() -> None:
    with pytest.raises(ValueError, match="fr"):
        load_catalog("fr")


def test_flatten_turns_tables_into_dotted_keys() -> None:
    assert flatten({"a": {"b": "x", "c": {"d": "y"}}, "e": "z"}) == {
        "a.b": "x",
        "a.c.d": "y",
        "e": "z",
    }


@pytest.mark.parametrize(
    ("cli", "settings", "expected"),
    [
        ("es", "en", "es"),
        (None, "es", "es"),
        (None, None, "en"),
        (None, "fr", "en"),
        ("", None, "en"),
    ],
)
def test_language_resolution_follows_adr_0017(
    cli: str | None, settings: str | None, expected: str
) -> None:
    assert resolve_language(cli, settings) == expected
