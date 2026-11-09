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
MERGE_FOLDER = "OutputUnif"  # a merge's file (feature 026)
FOLDERS = {"convert": MARKDOWN_FOLDER, "split": SPLIT_FOLDER, "merge": MERGE_FOLDER}


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
    tool: str = "convert"  # or "split" (023), "merge" (026): what the batch did
    cleaned: tuple[Entry, ...] = ()  # converted, with only good news to tell (audit 2026-11-08)

    @property
    def folder(self) -> str:
        return FOLDERS[self.tool]

    @property
    def has_files(self) -> bool:
        """Whether there are files to point at: "where" is said only then (audit B4-04)."""
        return bool(self.converted or self.kept)

    @property
    def where_key(self) -> str:
        return "summary.where" if self.tool == "convert" else f"summary.where_{self.tool}"

    @property
    def done_key(self) -> str:
        return "summary.converted" if self.tool == "convert" else f"summary.{self.tool}_done"
