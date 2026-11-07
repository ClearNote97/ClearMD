"""EN/ES message catalogs shared by backend and frontend (ADR-0012, ADR-0017). Stdlib only."""

import tomllib
import unicodedata
from collections.abc import Mapping
from importlib import resources
from typing import Any, Protocol

SUPPORTED_LANGUAGES = ("en", "es")
DEFAULT_LANGUAGE = "en"

# Controls (Cc), format characters (Cf: bidi overrides, zero-width), line and paragraph separators
# (Zl, Zp) and surrogates (Cs, from undecodable file names): invisible, able to drive a terminal,
# to reorder what the user reads, or to split a line where str.splitlines() does (reviews of 001).
_HIDDEN_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Zl", "Zp"})


def _escape(character: str) -> str:
    code = ord(character)
    return f"\\x{code:02x}" if code < 0x100 else f"\\u{code:04x}"


def printable(text: str) -> str:
    """``text`` with every invisible or line-breaking character shown as an escape (``\\x1b``)."""
    return "".join(
        _escape(char) if unicodedata.category(char) in _HIDDEN_CATEGORIES else char for char in text
    )


class _HasCatalogKeys(Protocol):
    @property
    def message_key(self) -> str: ...

    @property
    def action_key(self) -> str: ...


class Catalog:
    def __init__(self, language: str, messages: Mapping[str, str]) -> None:
        self.language = language
        self._messages = dict(messages)

    def keys(self) -> set[str]:
        return set(self._messages)

    def text_template(self, key: str) -> str:
        """The raw message, placeholders unfilled."""
        return self._messages[key]

    def text(self, key: str, **values: object) -> str:
        """The message ``key`` with its named placeholders filled. A missing key is a bug."""
        return self._messages[key].format(**values)

    def error(self, code: _HasCatalogKeys) -> str:
        """What happened and what to do, in one sentence pair (ADR-0013)."""
        return f"{self.text(code.message_key)} {self.text(code.action_key)}"

    def duration(self, seconds: float) -> str:
        """An estimate in plain words: never seconds, pages/s or MB/s (UX contract)."""
        if seconds < 60:
            return self.text("time.under_a_minute")
        minutes = round(seconds / 60)
        if minutes < 60:
            return self.text("time.minutes", minutes=minutes)
        return self.text("time.hours", hours=minutes // 60, minutes=minutes % 60)

    def clock(self, seconds: float) -> str:
        """Elapsed time as on a stopwatch: ``1:24``, ``10:00``, ``1:02:05``."""
        whole = int(seconds)
        hours, rest = divmod(whole, 3600)
        minutes, secs = divmod(rest, 60)
        return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"

    def gigabytes(self, size: int) -> str:
        """``6.9 GB`` / ``6,9 GB``: the decimal mark follows the language."""
        value = f"{size / 1024**3:.1f}"
        return f"{value.replace('.', self.text('number.decimal_mark'))} GB"

    def size(self, size: int) -> str:
        """A size as a person reads it: ``300 MB`` under a gigabyte, else ``1.5 GB``."""
        if size < 1024**3:
            return f"{self.count(max(1, round(size / 1024**2)))} MB"
        return self.gigabytes(size)

    def count(self, number: int) -> str:
        """``80,000`` / ``80.000``: the thousands mark follows the language."""
        return f"{number:,}".replace(",", self.text("number.thousands_mark"))

    def plural(self, key: str, number: int, **values: object) -> str:
        """English and Spanish need two forms: ``key.one``, and ``key.other`` for every other
        number (``{count}`` is the number, as the language writes it)."""
        form = "one" if number == 1 else "other"
        return self.text(f"{key}.{form}", count=self.count(number), **values)

    def totals(
        self, converted: int, skipped: int, failed: int, stopped: int = 0, *, split: bool = False
    ) -> str:
        """ "2 converted · 1 skipped · 0 failed", singular and plural; stopped only when any.
        A Split batch counts what was split (feature 023)."""
        parts = [
            self.plural("summary.count.split" if split else "summary.count.converted", converted),
            self.plural("summary.count.skipped", skipped),
            self.plural("summary.count.failed", failed),
        ]
        if stopped:
            parts.append(self.plural("summary.count.stopped", stopped))
        return " · ".join(parts)


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
