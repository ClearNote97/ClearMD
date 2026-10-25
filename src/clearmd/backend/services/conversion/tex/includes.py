r"""``\input``, ``\include`` and ``\subfile``, followed only inside the document folder (ADR-0022).

Paths resolve against the folder of the main file, as LaTeX does. Refusals are decided before
touching the disk when the argument alone says enough (absolute, ``..``, a drive or a scheme);
then every path component is checked with ``lstat`` so that no link or junction can lead outside,
and the file is read by walking the same components again with ``O_NOFOLLOW`` relative to each
folder's descriptor, so the file read is the file checked (on Windows, its identity is compared).
"""

import os
import re
import stat
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.notes import NoteReason
from clearmd.backend.services.conversion.safe_files import NotARegularFile

MAX_DEPTH = 8
MAX_FILES = 200
MAX_BYTES = Limits().max_file_size
_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_NO_FOLLOW = getattr(os, "O_NOFOLLOW", 0)
_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
_BINARY = getattr(os, "O_BINARY", 0)
_DRIVE = re.compile(r"^[A-Za-z]:")


class TooLarge(OSError):
    """The file would exceed what is left of the document's byte budget."""


@dataclass
class IncludeState:
    """Shared by every file of one document: the stack (cycles, depth) and the totals read."""

    folder: Path
    stack: list[tuple[int, int]] = field(default_factory=list)  # (device, inode): no name tricks
    files: int = 0
    bytes_read: int = 0


@dataclass(frozen=True)
class Entered:
    path: Path
    data: bytes
    identity: tuple[int, int]


def identity(path: Path) -> tuple[int, int]:
    """The file itself, whatever name reached it (case, ``./``, hard links)."""
    status = os.stat(path)
    return status.st_dev, status.st_ino


def _is_link(status: os.stat_result) -> bool:
    return stat.S_ISLNK(status.st_mode) or bool(
        getattr(status, "st_file_attributes", 0) & _REPARSE_POINT
    )


def walk_inside(folder: Path, relative: PurePosixPath) -> Path | NoteReason:
    """``folder/relative`` if every component exists and none is a link, else why not."""
    current = folder
    try:
        for part in relative.parts:
            current = current / part
            if _is_link(os.lstat(current)):
                return NoteReason.LINK
        if not stat.S_ISREG(os.lstat(current).st_mode):
            return NoteReason.MISSING
        if not current.resolve().is_relative_to(folder.resolve()):
            return NoteReason.OUTSIDE_FOLDER
    except (OSError, ValueError):  # missing, a name the OS rejects
        return NoteReason.MISSING
    return current


def is_outside_by_name(name: str) -> NoteReason | None:
    """Why ``name`` cannot be inside the folder, from the name alone (no disk access)."""
    if "\x00" in name:
        return NoteReason.MISSING
    parts = PurePosixPath(name).parts
    if name.startswith(("/", "~")) or _DRIVE.match(name) or any(":" in part for part in parts):
        return NoteReason.ABSOLUTE  # also "C:x", "http:", a drive in the middle
    if ".." in parts:
        return NoteReason.PARENT_SEGMENT
    return None


def _open_by_descriptors(folder: Path, relative: PurePosixPath) -> int:
    directory = os.open(folder, os.O_RDONLY | _DIRECTORY)
    try:
        for part in relative.parts[:-1]:
            inner = os.open(part, os.O_RDONLY | _DIRECTORY | _NO_FOLLOW, dir_fd=directory)
            os.close(directory)
            directory = inner
        return os.open(relative.parts[-1], os.O_RDONLY | _NO_FOLLOW, dir_fd=directory)
    finally:
        os.close(directory)


def _open_and_compare(folder: Path, relative: PurePosixPath) -> int:
    path = folder.joinpath(*relative.parts)
    descriptor = os.open(path, os.O_RDONLY | _BINARY)
    opened, checked = os.fstat(descriptor), os.lstat(path)
    same = (opened.st_dev, opened.st_ino) == (checked.st_dev, checked.st_ino)
    if not same or _is_link(checked) or not path.resolve().is_relative_to(folder.resolve()):
        os.close(descriptor)
        raise NotARegularFile(f"changed while it was opened: {path}")
    return descriptor


def read_inside(folder: Path, relative: PurePosixPath, max_bytes: int) -> bytes:
    """The bytes of ``folder/relative``, never through a link; ``TooLarge`` past ``max_bytes``."""
    if os.open in os.supports_dir_fd and _NO_FOLLOW:
        descriptor = _open_by_descriptors(folder, relative)
    else:
        descriptor = _open_and_compare(folder, relative)
    with os.fdopen(descriptor, "rb") as stream:
        status = os.fstat(stream.fileno())
        if not stat.S_ISREG(status.st_mode):
            raise NotARegularFile(f"not a regular file: {relative}")
        if status.st_size > max_bytes:
            raise TooLarge(f"larger than {max_bytes} bytes: {relative}")
        data = stream.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise TooLarge(f"larger than {max_bytes} bytes: {relative}")
    return data


def resolve_include(argument: str, state: IncludeState) -> Path | NoteReason:
    """The file an include names, or why it is not followed (cycles and limits: ``enter``)."""
    name = argument.strip().replace("\\", "/")
    if not name:
        return NoteReason.MISSING
    refused = is_outside_by_name(name)
    if refused is not None:
        return refused
    relative = PurePosixPath(name)
    if relative.suffix.lower() == ".tex":
        return walk_inside(state.folder, relative)
    # Like LaTeX: "chapter" means "chapter.tex"; "data.csv" is not a LaTeX file.
    with_tex = walk_inside(state.folder, PurePosixPath(f"{name}.tex"))
    if isinstance(with_tex, Path) or not relative.suffix:
        return with_tex
    return NoteReason.NOT_TEX


def enter(argument: str, state: IncludeState) -> Entered | NoteReason:
    """Resolve, check cycles and limits, and read the included file (once, on the budget)."""
    found = resolve_include(argument, state)
    if not isinstance(found, Path):
        return found
    try:
        found_identity = identity(found)
    except (OSError, ValueError):
        return NoteReason.MISSING
    if found_identity in state.stack:
        return NoteReason.CYCLE
    if len(state.stack) > MAX_DEPTH:
        return NoteReason.TOO_DEEP
    if state.files >= MAX_FILES:
        return NoteReason.TOO_MANY
    relative = PurePosixPath(found.relative_to(state.folder).as_posix())
    try:
        data = read_inside(state.folder, relative, max(MAX_BYTES - state.bytes_read, 0))
    except TooLarge:
        return NoteReason.TOO_LARGE
    except (OSError, ValueError):
        return NoteReason.MISSING
    state.files += 1
    state.bytes_read += len(data)
    return Entered(found.resolve(), data, found_identity)
