"""Inspect a ZIP-based document from its central directory, without decompressing it (ADR-0015).

docx, pptx, xlsx and epub are ZIP archives: a few KB on disk can expand to gigabytes (a zip bomb).
``zipfile.ZipFile`` reads only the index when opened; no entry is ever read here.
"""

import zipfile
from dataclasses import dataclass
from pathlib import Path

from clearmd.backend.schemas.limits import Limits

# Entries that hold the document's text; images and other media are not processed by the converters.
TEXT_SUFFIXES = (".xml", ".xhtml", ".html", ".htm", ".rels")


@dataclass(frozen=True)
class ArchiveInfo:
    uncompressed: int
    text_bytes: int
    file_size: int

    @property
    def ratio(self) -> float:
        """Uncompressed total over the whole file's size (never per entry)."""
        return self.uncompressed / self.file_size if self.file_size else 0.0


def inspect_archive(path: Path) -> ArchiveInfo | None:
    """Sizes from the archive's index, or ``None`` when it is not a readable ZIP."""
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
        file_size = path.stat().st_size
    except (zipfile.BadZipFile, OSError):
        return None
    return ArchiveInfo(
        uncompressed=sum(entry.file_size for entry in entries),
        text_bytes=sum(
            entry.file_size for entry in entries if entry.filename.lower().endswith(TEXT_SUFFIXES)
        ),
        file_size=file_size,
    )


def is_unsafe(info: ArchiveInfo, limits: Limits) -> bool:
    return info.uncompressed > limits.max_uncompressed or info.ratio > limits.max_ratio
