"""EN/ES message catalogs shared by backend and frontend (ADR-0012, ADR-0017). Stdlib only."""

import tomllib
from collections.abc import Mapping
from importlib import resources
from typing import Any, Protocol

SUPPORTED_LANGUAGES = ("en", "es")
DEFAULT_LANGUAGE = "en"


class _HasCatalogKeys(Protocol):
    @property
    def message_key(self) -> str: ...

    @property
    def action_key(self) -> str: ...


class Catalog:
    def __init__(self, language: str, messages: Mapping[str, str]) -> None:
        self.language = language
        self._messages = dict(messages)

    def text(self, key: str, **values: object) -> str:
        """The message ``key`` with its named placeholders filled. A missing key is a bug."""
        return self._messages[key].format(**values)

    def error(self, code: _HasCatalogKeys) -> str:
        """What happened and what to do, in one sentence pair (ADR-0013)."""
        return f"{self.text(code.message_key)} {self.text(code.action_key)}"


def flatten(table: Mapping[str, Any], prefix: str = "") -> dict[str, str]:
    """TOML tables to flat dotted keys: ``{"a": {"b": "x"}}`` → ``{"a.b": "x"}``."""
    flat: dict[str, str] = {}
    for key, value in table.items():
        name = f"{prefix}{key}"
        if isinstance(value, Mapping):
            flat.update(flatten(value, f"{name}."))
        else:
            flat[name] = str(value)
    return flat


def load_catalog(language: str) -> Catalog:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"unsupported language: {language!r}")
    source = resources.files(__name__).joinpath(f"{language}.toml").read_text(encoding="utf-8")
    return Catalog(language, flatten(tomllib.loads(source)))


def resolve_language(cli_language: str | None, settings_language: str | None) -> str:
    """``--lang`` for this run, then the setting, then English (ADR-0017)."""
    for candidate in (cli_language, settings_language):
        if candidate in SUPPORTED_LANGUAGES:
            return candidate
    return DEFAULT_LANGUAGE
