"""The preferences shared by every interface, with their defaults (ADR-0012, ADR-0017)."""

import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


@dataclass(frozen=True)
class Settings:
    language: str = "en"
    theme: str = "system"
    open_output_when_done: bool = True
    on_existing_output: str = "ask"
    recursive: bool = True
    html_strategy: str = "full"
    show_welcome: bool = True
    summary_format: str = "markdown"  # or "markdown_pdf": Resumen_ClearMD.pdf too (ADR-0031)
    # The folder the user last picked for the results; empty: next to the originals (ADR-0016/0026).
    last_output_folder: str = ""


# The accepted values of each text setting; booleans accept only true/false.
CHOICES: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "language": frozenset({"en", "es"}),
        "theme": frozenset({"system", "light", "dark"}),
        "on_existing_output": frozenset({"ask", "overwrite", "skip"}),
        "html_strategy": frozenset({"full", "article"}),
        "summary_format": frozenset({"markdown", "markdown_pdf"}),
    }
)


# Settings that hold a path the user chose, not one of a few choices: any plain text up to a length.
PATH_SETTINGS: frozenset[str] = frozenset({"last_output_folder"})
MAX_PATH_LENGTH = 4096


def valid_path_setting(value: str) -> bool:
    """Whether a path can be stored in settings.toml: plain text (no control characters, no lone
    surrogates from an undecodable name) and a sane length. A folder that fails this can still
    receive results; it is just not remembered (security review of 005)."""
    return len(value) <= MAX_PATH_LENGTH and not any(
        unicodedata.category(char) in {"Cc", "Cs"} for char in value
    )


class SettingsProblem(StrEnum):
    UNKNOWN_KEY = "unknown_key"
    INVALID_VALUE = "invalid_value"
    UNREADABLE = "unreadable"


@dataclass(frozen=True)
class SettingsWarning:
    """One line for the user: a setting was ignored and its default used (AC-33)."""

    key: str
    problem: SettingsProblem
