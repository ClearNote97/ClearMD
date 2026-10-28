"""What a view draws: plain data, every text already written in the user's language."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from clearmd.frontend.presenter.state import Action, AppState


@dataclass(frozen=True)
class StateView:
    state: AppState
    label: str
    enabled: frozenset[Action]
    step: int  # 1 Choose, 2 Review, 3 Convert, 4 Results (ADR-0027: the rail highlights it)


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


@dataclass(frozen=True)
class PlanView:
    summary: str
    rows: tuple[PlanRow, ...]
    asks_about_existing: bool  # the user chooses: overwrite or keep (setting "ask")


@dataclass(frozen=True)
class ProgressView:
    counter: str  # "3 of 37"
    name: str
    fraction: float  # 0..1, of the files done
    time_left: str | None  # "about 3 min left"
    elapsed: str | None  # this file's running timer, once it takes long
    long_file: str | None  # "Large files can take a few minutes."


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
