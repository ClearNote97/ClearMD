"""The summary's data: what a summary says, once, for every format (ADR-0031).

Plain frozen dataclasses and constants; the builder that fills them is ``content``. They stand
apart so that the writers (Markdown, PDF) import the shape without the builder's inputs.
"""

from dataclasses import dataclass
from enum import StrEnum

from clearmd.backend.schemas.notes import ConversionNote

DATE_FORMAT = "%Y-%m-%d %H:%M"
MARKDOWN_FOLDER = "OutputMD"
SPLIT_FOLDER = "OutputSep"  # a split batch's parts (feature 023)


class Mark(StrEnum):
    """How it went: the whole batch, or one file."""

    DONE = "done"  # ✅ everything converted
    ATTENTION = "attention"  # ⚠️ converted, with something to look at
    FAILED = "failed"  # ❌ not converted
    STOPPED = "stopped"  # ⏹️ stopped at its limit, or the batch cancelled


@dataclass(frozen=True)
class Entry:
    """One file in a list: its name and folder (from the user's files), what happened and what
    to do (the catalog's), its notes, and a technical detail."""

    mark: Mark | None
    name: str
    folder: str  # relative to where the batch started; "" in the top folder
    message: str = ""
    notes: tuple[ConversionNote, ...] = ()
    detail: str = ""
    result: str = ""  # a kept result's name, in ``folder`` of the Markdown folder


@dataclass(frozen=True)
class Row:
    """A converted file: the table's row."""

    name: str
    folder: str
    result: str  # the Markdown file's name, in ``folder`` of the Markdown folder
    format: str
    time: str


@dataclass(frozen=True)
class SummaryContent:
    mark: Mark
    headline: str
    attention_line: str  # "" when nothing needs attention
    batch_line: str  # date · version · totals: the history is made of these
    attention: tuple[Entry, ...]
    converted: tuple[Row, ...]
    left_out: tuple[Entry, ...]
    kept: tuple[Entry, ...]
    cancelled: tuple[Entry, ...]
    split: bool = False  # a Split batch (feature 023): its parts are in OutputSep

    @property
    def folder(self) -> str:
        return SPLIT_FOLDER if self.split else MARKDOWN_FOLDER

    @property
    def where_key(self) -> str:
        return "summary.where_split" if self.split else "summary.where"

    @property
    def done_key(self) -> str:
        return "summary.split_done" if self.split else "summary.converted"
