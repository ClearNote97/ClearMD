"""Expand the inputs into candidate files and skipped items (ADR-0010, AC-02 - AC-08).

Untrusted input: symbolic links are never followed, ClearMD_Output folders are never entered and
hidden items are left out. A skipped folder is reported once, never file by file.
"""

import os
import stat
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.events import ScanProgress
from clearmd.backend.schemas.formats import MARKDOWN_EXTENSIONS, OUTPUT_DIR_NAME, ZIP_EXTENSIONS
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.models import InputError, InputProblem, SkippedItem

LOCK_FILE_PREFIX = "~$"
_HIDDEN_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 2)


@dataclass(frozen=True)
class Candidate:
    """A file that passed the scanning rules; detection decides whether it is convertible."""

    path: Path
    input: Path
    relative_dir: Path
    input_is_dir: bool
    size: int


@dataclass(frozen=True)
class ScanResult:
    candidates: tuple[Candidate, ...]
    skipped: tuple[SkippedItem, ...]
    input_errors: tuple[InputError, ...]


def is_hidden(name: str, status: os.stat_result) -> bool:
    """A leading dot, or the Windows hidden attribute (absent elsewhere)."""
    attributes = getattr(status, "st_file_attributes", 0)
    return name.startswith(".") or bool(attributes & _HIDDEN_ATTRIBUTE)


def _file_rule(path: Path, size: int, limits: Limits) -> SkipReason | None:
    if path.name.startswith(LOCK_FILE_PREFIX):
        return SkipReason.LOCK_FILE
    suffix = path.suffix.lower()
    if suffix in MARKDOWN_EXTENSIONS:
        return SkipReason.ALREADY_MARKDOWN
    if suffix in ZIP_EXTENSIONS:
        return SkipReason.ZIP_ARCHIVE
    if size > limits.max_file_size:
        return SkipReason.TOO_LARGE
    return None


def _sorted_entries(folder: Path) -> list[os.DirEntry[str]]:
    with os.scandir(folder) as entries:
        return sorted(entries, key=lambda entry: (entry.name.casefold(), entry.name))


class _Scanner:
    def __init__(
        self,
        *,
        recursive: bool,
        limits: Limits,
        on_progress: Callable[[ScanProgress], None] | None,
    ) -> None:
        self.recursive = recursive
        self.limits = limits
        self.on_progress = on_progress
        self.candidates: list[Candidate] = []
        self.skipped: list[SkippedItem] = []
        self.errors: list[InputError] = []

    def add_input(self, source: Path) -> None:
        if source.is_symlink():
            self.skipped.append(SkippedItem(source, SkipReason.SYMLINK))
        elif not source.exists():
            self.errors.append(InputError(source, InputProblem.NOT_FOUND))
        elif source.is_dir():
            if source.name.casefold() == OUTPUT_DIR_NAME.casefold():
                self.skipped.append(SkippedItem(source, SkipReason.OUTPUT_FOLDER, is_dir=True))
            else:
                self._walk(source, source, Path())
        else:
            self._add_file(source, source, Path(), source.stat().st_size, input_is_dir=False)

    def _add_file(
        self, path: Path, origin: Path, relative: Path, size: int, *, input_is_dir: bool
    ) -> None:
        reason = _file_rule(path, size, self.limits)
        if reason is not None:
            self.skipped.append(SkippedItem(path, reason))
        else:
            self.candidates.append(Candidate(path, origin, relative, input_is_dir, size))

    def _walk(self, origin: Path, folder: Path, relative: Path) -> None:
        if self.on_progress is not None:
            self.on_progress(ScanProgress(found=len(self.candidates), current=folder))
        try:
            entries = _sorted_entries(folder)
        except PermissionError:
            self.skipped.append(SkippedItem(folder, SkipReason.UNREADABLE, is_dir=True))
            return
        subfolders: list[tuple[Path, Path]] = []
        for entry in entries:
            path = Path(entry.path)
            if entry.is_symlink():
                self.skipped.append(SkippedItem(path, SkipReason.SYMLINK))
                continue
            status = entry.stat(follow_symlinks=False)
            if entry.is_dir(follow_symlinks=False):
                if entry.name.casefold() == OUTPUT_DIR_NAME.casefold():
                    self.skipped.append(SkippedItem(path, SkipReason.OUTPUT_FOLDER, is_dir=True))
                elif is_hidden(entry.name, status):
                    self.skipped.append(SkippedItem(path, SkipReason.HIDDEN, is_dir=True))
                elif self.recursive:
                    subfolders.append((path, relative / entry.name))
            elif is_hidden(entry.name, status):
                self.skipped.append(SkippedItem(path, SkipReason.HIDDEN))
            elif entry.is_file(follow_symlinks=False):
                self._add_file(path, origin, relative, status.st_size, input_is_dir=True)
        for path, sub_relative in subfolders:
            self._walk(origin, path, sub_relative)


def scan(
    inputs: Sequence[Path],
    *,
    recursive: bool,
    limits: Limits,
    on_progress: Callable[[ScanProgress], None] | None = None,
) -> ScanResult:
    """Files of every input, in a stable order: files of a folder before its subfolders."""
    scanner = _Scanner(recursive=recursive, limits=limits, on_progress=on_progress)
    for source in inputs:
        scanner.add_input(source)
    return ScanResult(tuple(scanner.candidates), tuple(scanner.skipped), tuple(scanner.errors))
