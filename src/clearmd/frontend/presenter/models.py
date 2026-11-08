"""What a view draws: plain data, every text already written in the user's language."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from clearmd.frontend.presenter.state import Action, AppState, Tool


@dataclass(frozen=True)
class Primary:
    """The page's primary action (ADR-0029): its label, whether it can run, and why not."""

    label: str
    enabled: bool
    hint: str = ""  # one line, only when it is disabled


@dataclass(frozen=True)
class StateView:
    state: AppState
    label: str
    enabled: frozenset[Action]
    step: int  # 1 Choose, 2 Review, 3 Convert, 4 Results: where the batch is
    page: int = 1  # the step on screen (ADR-0029: every step can be opened); 0: Home (023)
    primary: Primary = Primary("", False)
    tool: Tool = Tool.CONVERT  # what the batch does (feature 023)


@dataclass(frozen=True)
class InputRow:
    path: Path
    name: str
    location: str  # the folder it is in, as the user would read it
    is_folder: bool
    icon: str  # an asset name under frontend/assets/icons (presenter.icons)


class OutputMode(StrEnum):
    NEXT_TO = "next_to"  # ClearMD_Output next to the originals (the default, ADR-0016)
    FOLDER = "folder"  # in a folder the user picked


@dataclass(frozen=True)
class OutputChoice:
    mode: OutputMode
    folder: Path | None  # the chosen folder, in FOLDER mode
    suggestion: Path | None  # the folder remembered from last time, offered when picking
    label: str
    summary_format: str = "markdown"  # or "markdown_pdf" (ADR-0031), or "pdf" (020)
    images: str = "omit"  # or "folder" (ADR-0033)
    # Split (feature 023): its choices are shown in place of the images.
    tool: Tool = Tool.CONVERT
    split_cut: str = "parts"  # or "pages"
    split_parts: int = 2
    split_pages: int = 50
    split_keep: str = "both"  # or "pdf", "markdown"
    split_words: int = 30_000  # parts of about N words (feature 024)
    merge_into: str = "markdown"  # or "pdf": Merge's choice, in place of the images (026)


class RowKind(StrEnum):
    CONVERT = "convert"
    EXISTS = "exists"  # will be converted; its output already exists
    SKIPPED = "skipped"
    MISSING = "missing"  # an input that is not there


@dataclass(frozen=True)
class PlanRow:
    kind: RowKind
    name: str
    location: str
    detail: str  # the format, or why it is skipped and what to do
    icon: str


class Tone(StrEnum):
    """How a figure is coloured: the accent, a warning, a problem, or plain."""

    ACCENT = "accent"
    WARNING = "warning"
    DANGER = "danger"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class Stat:
    """One figure of a summary ("To convert: 12"), drawn as a card by the GUIs."""

    label: str
    value: int
    tone: Tone


@dataclass(frozen=True)
class PlanView:
    summary: str
    rows: tuple[PlanRow, ...]
    asks_about_existing: bool  # the user chooses: overwrite or keep (setting "ask")
    stats: tuple[Stat, ...] = ()
    plan_id: int = 0  # another plan (even with the same rows): the user's answer starts over
    split_offer: str = ""  # "Split the Large PDFs (2)"; empty: none to offer (feature 025)


@dataclass(frozen=True)
class ProgressView:
    counter: str  # "3 of 37"
    name: str
    fraction: float  # 0..1, of the files done
    time_left: str | None  # "about 3 min left"
    elapsed: str | None  # this file's running timer, once it takes long
    long_file: str | None  # "Large files can take a few minutes."
    icon: str = "unknown"  # the current file's icon


@dataclass(frozen=True)
class ResultRow:
    name: str
    location: str
    detail: str  # what happened and what to do
    icon: str


@dataclass(frozen=True)
class ResultView:
    headline: str
    counts: str
    rows: tuple[ResultRow, ...]
    folders: tuple[Path, ...]  # the ClearMD_Output folders of the batch
    stats: tuple[Stat, ...] = ()
    split_offer: str = ""  # "Split the Large PDFs (1)"; empty: none to offer (feature 025)
