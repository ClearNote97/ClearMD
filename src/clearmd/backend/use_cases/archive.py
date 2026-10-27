"""Inspect a ZIP-based document from its central directory, without decompressing it (ADR-0015).

docx, pptx, xlsx and epub are ZIP archives: a few KB on disk can expand to gigabytes (a zip bomb).
``zipfile.ZipFile`` reads only the index when opened; no entry is ever read here.
"""

import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.limits import Limits

# Entries that hold the document's text; images and other media are not processed by the converters.
TEXT_SUFFIXES = (".xml", ".xhtml", ".html", ".htm", ".rels")
# Indices of zipfile's end-of-central-directory record (``zipfile._ECD_*``).
_ENTRIES_TOTAL = 4
_DIRECTORY_SIZE = 5

# Real documents have a central directory of a few KB; 50,000 entries of ~1 KB each fit in this.
MAX_DIRECTORY_BYTES = 64 * 1024**2


@dataclass(frozen=True)
class ArchiveInfo:
    uncompressed: int
    text_bytes: int
    file_size: int
    entries: int

    @property
    def ratio(self) -> float:
        """Uncompressed total over the whole file's size (never per entry)."""
        return self.uncompressed / self.file_size if self.file_size else 0.0


def _end_record(path: Path) -> tuple[int, int] | None:
    """(entries, central directory size) exactly as ``zipfile`` will read them, or ``None``.

    Uses the stdlib's own locator (private, guarded by a test), ZIP64 included: a hand-written
    parser can be fooled into a different answer than the one ``zipfile`` acts on (adversarial
    review of feature 001). Nothing but the file's tail is read.
    """
    with path.open("rb") as stream:
        record = zipfile._EndRecData(stream)  # type: ignore[attr-defined]  # guarded by a test
    if record is None:
        return None
    return int(record[_ENTRIES_TOTAL]), int(record[_DIRECTORY_SIZE])


def inspect_archive(path: Path, max_entries: int = 50_000) -> ArchiveInfo | None:
    """Sizes from the archive's index, or ``None`` when it is not a ZIP at all.

    The entry count and the central directory size are checked before ``zipfile`` loads the index
    (one object per entry, in the interface's process).
    """
    try:
        file_size = path.stat().st_size
        end = _end_record(path)
        if end is None:
            return None  # zipfile cannot open it either: the converter fails it as corrupt
        entries, directory = end
        if entries > max_entries or directory > MAX_DIRECTORY_BYTES:
            return ArchiveInfo(0, 0, file_size, entries=max(entries, max_entries + 1))
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
    except (zipfile.BadZipFile, OSError, ValueError, struct.error):
        return None
    return ArchiveInfo(
        uncompressed=sum(entry.file_size for entry in infos),
        text_bytes=sum(
            entry.file_size for entry in infos if entry.filename.lower().endswith(TEXT_SUFFIXES)
        ),
        file_size=file_size,
        entries=len(infos),
    )


def unsafe_reason(info: ArchiveInfo, limits: Limits) -> tuple[SkipReason, float, float] | None:
    """The first check the archive fails, with its value and the limit; ``None`` when it passes."""
    if info.entries > limits.max_zip_entries:
        return SkipReason.ARCHIVE_ENTRIES, info.entries, limits.max_zip_entries
    if info.uncompressed > limits.max_uncompressed:
        return SkipReason.ARCHIVE_TOO_LARGE, info.uncompressed, limits.max_uncompressed
    if info.ratio > limits.max_ratio:
        return SkipReason.ARCHIVE_RATIO, info.ratio, limits.max_ratio
    return None


def is_unsafe(info: ArchiveInfo, limits: Limits) -> bool:
    return unsafe_reason(info, limits) is not None
