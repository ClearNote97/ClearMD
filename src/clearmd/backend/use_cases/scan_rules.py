"""The scanning rules: what a file or a folder entry is (hidden, link, locked, too large).

Pure functions of a name, a status or a size, and the one sorted listing of a folder, so
that ``scanning`` keeps the walk. Stdlib and schemas only.
"""

import os
import stat
from pathlib import Path

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.formats import MARKDOWN_EXTENSIONS, ZIP_EXTENSIONS
from clearmd.backend.schemas.limits import Limits

LOCK_FILE_PREFIX = "~$"
# Folders below an input deeper than this are skipped (real trees are far shallower; an archive
# can nest thousands to exhaust the walk).
MAX_DEPTH = 100
HIDDEN_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 2)


def is_hidden(name: str, status: os.stat_result) -> bool:
    """A leading dot, or the Windows hidden attribute (absent elsewhere)."""
    attributes = getattr(status, "st_file_attributes", 0)
    return name.startswith(".") or bool(attributes & HIDDEN_ATTRIBUTE)


def is_link_entry(entry: os.DirEntry[str]) -> bool:
    """A symbolic link, or a Windows junction (which ``is_symlink`` does not report)."""
    is_junction = getattr(entry, "is_junction", None)
    return entry.is_symlink() or bool(is_junction and is_junction())


def file_rule(
    path: Path, size: int, limits: Limits, *, markdown: bool = False
) -> SkipReason | None:
    """Why a file is left out, or ``None``. ``markdown``: Markdown is taken (Split, 024)."""
    if path.name.startswith(LOCK_FILE_PREFIX):
        return SkipReason.LOCK_FILE
    suffix = path.suffix.lower()
    if suffix in MARKDOWN_EXTENSIONS and not markdown:
        return SkipReason.ALREADY_MARKDOWN
    if suffix in ZIP_EXTENSIONS:
        return SkipReason.ZIP_ARCHIVE
    if size > limits.max_file_size:
        return SkipReason.TOO_LARGE
    return None


def sorted_entries(folder: Path) -> list[os.DirEntry[str]]:
    with os.scandir(folder) as entries:
        return sorted(entries, key=lambda entry: (entry.name.casefold(), entry.name))
