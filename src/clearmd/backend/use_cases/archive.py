"""Inspect a ZIP-based document from its central directory, without decompressing it (ADR-0015).

docx, pptx, xlsx and epub are ZIP archives: a few KB on disk can expand to gigabytes (a zip bomb).
``zipfile.ZipFile`` reads only the index when opened; no entry is ever read here.
"""

import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path

from clearmd.backend.schemas.limits import Limits

# Entries that hold the document's text; images and other media are not processed by the converters.
TEXT_SUFFIXES = (".xml", ".xhtml", ".html", ".htm", ".rels")

_END_SIGNATURE = b"PK\x05\x06"
_END_SIZE = 22
_MAX_COMMENT = 0xFFFF
_ZIP64_MARK = 0xFFFF


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


def declared_entries(path: Path) -> int | None:
    """The entry count the end record declares, read from the file's tail only.

    Loading the central directory builds one object per entry, so an archive of millions of tiny
    entries is refused before ``zipfile`` reads it (security review of feature 001).
    """
    with path.open("rb") as stream:
        size = stream.seek(0, 2)
        tail_size = min(size, _END_SIZE + _MAX_COMMENT)
        stream.seek(size - tail_size)
        tail = stream.read(tail_size)
    position = tail.rfind(_END_SIGNATURE)
    if position < 0 or len(tail) - position < _END_SIZE:
        return None
    entries: int = struct.unpack_from("<H", tail, position + 10)[0]
    return entries


def inspect_archive(path: Path, max_entries: int = 50_000) -> ArchiveInfo | None:
    """Sizes from the archive's index, or ``None`` when it is not a readable ZIP."""
    try:
        file_size = path.stat().st_size
        declared = declared_entries(path)
        if declared is None:
            return None
        if declared > max_entries or declared == _ZIP64_MARK:
            return ArchiveInfo(0, 0, file_size, entries=declared)
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
    except (zipfile.BadZipFile, OSError):
        return None
    return ArchiveInfo(
        uncompressed=sum(entry.file_size for entry in infos),
        text_bytes=sum(
            entry.file_size for entry in infos if entry.filename.lower().endswith(TEXT_SUFFIXES)
        ),
        file_size=file_size,
        entries=len(infos),
    )


def is_unsafe(info: ArchiveInfo, limits: Limits) -> bool:
    return (
        info.entries > limits.max_zip_entries
        or info.entries == _ZIP64_MARK
        or info.uncompressed > limits.max_uncompressed
        or info.ratio > limits.max_ratio
    )
