r"""``\input``, ``\include`` and ``\subfile``, followed only inside the document folder (ADR-0022).

Paths resolve against the folder of the file being converted, as LaTeX does. Refusals are decided
before touching the disk when the argument alone says enough (absolute, ``..``); then every path
component is checked with ``lstat`` so that no link or junction can lead outside.
"""

import os
import re
import stat
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.notes import NoteReason
from clearmd.backend.services.conversion.safe_files import read_regular_file

MAX_DEPTH = 8
MAX_FILES = 200
MAX_BYTES = Limits().max_file_size
_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_DRIVE = re.compile(r"^[A-Za-z]:")


@dataclass
class IncludeState:
    """Shared by every file of one document: the stack (cycles, depth) and the totals read."""

    folder: Path
    stack: list[Path] = field(default_factory=list)
    files: int = 0
    bytes_read: int = 0


def _is_link(status: os.stat_result) -> bool:
    return stat.S_ISLNK(status.st_mode) or bool(
        getattr(status, "st_file_attributes", 0) & _REPARSE_POINT
    )


def _walk_inside(folder: Path, relative: PurePosixPath) -> Path | NoteReason:
    current = folder
    for part in relative.parts:
        current = current / part
        try:
            status = os.lstat(current)
        except FileNotFoundError:
            return NoteReason.MISSING
        except OSError:
            return NoteReason.MISSING
        if _is_link(status):
            return NoteReason.LINK
    if not stat.S_ISREG(os.lstat(current).st_mode):
        return NoteReason.MISSING
    if not current.resolve().is_relative_to(folder.resolve()):
        return NoteReason.OUTSIDE_FOLDER
    return current


def resolve_include(argument: str, state: IncludeState) -> Path | NoteReason:
    """The file an include names, or why it is not followed (cycles and limits: ``enter``)."""
    name = argument.strip().replace("\\", "/")
    if not name:
        return NoteReason.MISSING
    if name.startswith(("/", "~")) or _DRIVE.match(name):
        return NoteReason.ABSOLUTE
    relative = PurePosixPath(name)
    if ".." in relative.parts:
        return NoteReason.PARENT_SEGMENT
    if relative.suffix.lower() == ".tex":
        return _walk_inside(state.folder, relative)
    # Like LaTeX: "chapter" means "chapter.tex"; "data.csv" is not a LaTeX file.
    with_tex = _walk_inside(state.folder, PurePosixPath(f"{name}.tex"))
    if isinstance(with_tex, Path) or not relative.suffix:
        return with_tex
    return NoteReason.NOT_TEX


def enter(argument: str, state: IncludeState) -> tuple[Path, bytes] | NoteReason:
    """Resolve, check cycles and limits, and read the included file."""
    found = resolve_include(argument, state)
    if not isinstance(found, Path):
        return found
    real = found.resolve()
    if real in state.stack:
        return NoteReason.CYCLE
    if len(state.stack) > MAX_DEPTH:
        return NoteReason.TOO_DEEP
    if state.files >= MAX_FILES:
        return NoteReason.TOO_MANY
    room = MAX_BYTES - state.bytes_read
    try:
        data = read_regular_file(found, max(room, 0))
    except OSError:
        return NoteReason.TOO_LARGE if found.stat().st_size > room else NoteReason.MISSING
    state.files += 1
    state.bytes_read += len(data)
    return real, data
