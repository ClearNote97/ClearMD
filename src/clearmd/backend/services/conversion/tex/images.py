r"""``\includegraphics`` → a link that works from the output ``.md`` (AC-13).

LaTeX looks images up from the main file's folder, then in each ``\graphicspath`` entry, and adds
a known extension when there is none. The same lookup happens here, inside the document folder
only, for image files only, and without following links. An image that is not found keeps its
path as written; one that names something outside the folder or remote (``/x``, ``..``,
``C:``, ``http:``, ``//host``) is never a link, so opening the Markdown never fetches it.
"""

import os
import re
from pathlib import Path, PurePosixPath

from clearmd.backend.services.conversion.tex.includes import is_outside_by_name, walk_inside

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".pdf", ".svg", ".gif", ".webp", ".eps")
MAX_GRAPHICS_PATHS = 64
_GRAPHICSPATH = re.compile(r"\\graphicspath\s*\{((?:\s*\{[^{}\n]{0,512}\}){1,64})\s*\}")
_ENTRY = re.compile(r"\{([^{}\n]{0,512})\}")
_COMMENT = re.compile(r"(?<!\\)%[^\n]*")


def graphics_paths(source: str) -> list[str]:
    r"""The folders of every ``\graphicspath`` in ``source``, in order (at most 64)."""
    found: list[str] = []
    for group in _GRAPHICSPATH.findall(_COMMENT.sub("", source)):
        found.extend(entry.strip() for entry in _ENTRY.findall(group) if entry.strip())
    return found[:MAX_GRAPHICS_PATHS]


def _candidates(name: str) -> list[str]:
    if PurePosixPath(name).suffix.lower() in IMAGE_EXTENSIONS:
        return [name]
    return [name + extension for extension in IMAGE_EXTENSIONS]


def _find(name: str, folder: Path, prefixes: list[str]) -> Path | None:
    for prefix in ["", *prefixes]:
        for candidate in _candidates(prefix.rstrip("/") + "/" + name if prefix else name):
            if is_outside_by_name(candidate) is not None:
                continue
            found = walk_inside(folder, PurePosixPath(candidate))
            if isinstance(found, Path):
                return found
    return None


def image_link(argument: str, folder: Path, prefixes: list[str], target: Path) -> str | None:
    """The link to ``argument`` seen from ``target``'s folder; ``None`` if it must not be a link."""
    name = argument.strip().replace("\\", "/")
    if not name or is_outside_by_name(name) is not None:
        return None
    found = _find(name, folder, prefixes)
    if found is None:
        return argument.strip()
    try:
        return Path(os.path.relpath(found, start=target.parent)).as_posix()
    except ValueError:  # another drive on Windows: no relative path exists
        return argument.strip()


class ImageFinder:
    """``image_link`` for one document, each name looked up once."""

    def __init__(self, folder: Path, prefixes: list[str], target: Path) -> None:
        self._folder, self._prefixes, self._target = folder, prefixes, target
        self._seen: dict[str, str | None] = {}

    def link(self, argument: str) -> str | None:
        if argument not in self._seen:
            self._seen[argument] = image_link(argument, self._folder, self._prefixes, self._target)
        return self._seen[argument]
