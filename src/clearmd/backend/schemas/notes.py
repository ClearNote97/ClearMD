"""Conversion notes: language-neutral facts about what a converter could not do faithfully.

ADR-0022.

A note never holds a sentence: the summary and the interfaces turn it into words with the catalogs.
"""

from dataclasses import dataclass
from enum import StrEnum


class NoteKind(StrEnum):
    UNKNOWN_COMMANDS = "unknown_commands"
    INCLUDE_NOT_FOLLOWED = "include_not_followed"
    MACRO_LIMIT_REACHED = "macro_limit_reached"
    TABLE_KEPT_AS_LATEX = "table_kept_as_latex"
    ENCODING_GUESSED = "encoding_guessed"
    PARSE_RECOVERED = "parse_recovered"

    @property
    def key(self) -> str:
        return f"note.{self.value}"


class NoteReason(StrEnum):
    """Why something was not done; shown next to its subject."""

    OUTSIDE_FOLDER = "outside_folder"
    ABSOLUTE = "absolute"
    PARENT_SEGMENT = "parent_segment"
    LINK = "link"
    NOT_TEX = "not_tex"
    MISSING = "missing"
    CYCLE = "cycle"
    TOO_DEEP = "too_deep"
    TOO_MANY = "too_many"
    TOO_LARGE = "too_large"
    EXPANSIONS = "expansions"
    NESTING = "nesting"
    GROWTH = "growth"

    @property
    def key(self) -> str:
        return f"note.reason.{self.value}"


@dataclass(frozen=True)
class NoteItem:
    """What the note is about (a command, a path, an encoding...) and, optionally, why."""

    subject: str
    reason: str = ""


@dataclass(frozen=True)
class ConversionNote:
    kind: NoteKind
    items: tuple[NoteItem, ...] = ()
