r"""``\includegraphics`` → a link that works from the output ``.md`` (AC-13).

LaTeX looks images up from the main file's folder, then in each ``\graphicspath`` entry, and adds
a known extension when there is none. The same lookup happens here, inside the document folder
only and without following links; an image that is not found keeps its path as written.
"""

import os
import re
from pathlib import Path, PurePosixPath

from clearmd.backend.services.conversion.tex.includes import is_outside_by_name, walk_inside

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".pdf", ".svg", ".gif", ".webp", ".eps")
_GRAPHICSPATH = re.compile(r"\\graphicspath\s*\{((?:\s*\{[^{}]*\})+)\s*\}")
_ENTRY = re.compile(r"\{([^{}]*)\}")
_COMMENT = re.compile(r"(?<!\\)%.*")


def graphics_paths(source: str) -> list[str]:
    r"""The folders of every ``\graphicspath`` in ``source``, in order."""
    found: list[str] = []
    for group in _GRAPHICSPATH.findall(_COMMENT.sub("", source)):
        found.extend(entry.strip() for entry in _ENTRY.findall(group) if entry.strip())
    return found


def _candidates(name: str) -> list[str]:
    if PurePosixPath(name).suffix.lower() in IMAGE_EXTENSIONS:
        return [name]
    return [name, *(name + extension for extension in IMAGE_EXTENSIONS)]


def _find(name: str, folder: Path, prefixes: list[str]) -> Path | None:
    for prefix in ["", *prefixes]:
        for candidate in _candidates(prefix.rstrip("/") + "/" + name if prefix else name):
            if is_outside_by_name(candidate) is not None:
                continue
            found = walk_inside(folder, PurePosixPath(candidate))
            if isinstance(found, Path):
                return found
    return None


def image_link(argument: str, folder: Path, prefixes: list[str], target: Path) -> str:
    """The Markdown link target for ``argument`` seen from ``target``'s folder."""
    name = argument.strip().replace("\\", "/")
    if not name or is_outside_by_name(name) is not None:
        return argument.strip()
    found = _find(name, folder, prefixes)
    if found is None:
        return argument.strip()
    try:
        link = Path(os.path.relpath(found, start=target.parent)).as_posix()
    except ValueError:  # another drive on Windows: no relative path exists
        return argument.strip()
    return f"<{link}>" if " " in link else link
