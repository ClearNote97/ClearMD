"""The preferences shared by every interface, with their defaults (ADR-0012, ADR-0017)."""

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


# The accepted values of each text setting; booleans accept only true/false.
CHOICES: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "language": frozenset({"en", "es"}),
        "theme": frozenset({"system", "light", "dark"}),
        "on_existing_output": frozenset({"ask", "overwrite", "skip"}),
        "html_strategy": frozenset({"full", "article"}),
    }
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
