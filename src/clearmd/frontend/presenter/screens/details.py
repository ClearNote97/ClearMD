"""What "Copy Details" copies after an unexpected error (doubts board 2026-11-09, D3): the version,
the window, the system and the error, with every path and file name it can find replaced by
``<file>.ext``, because a report goes to a public page and names belong to people."""

import os
import platform
import re
from collections.abc import Iterable

from clearmd.i18n import Catalog

# A path starts at a drive (C:\\), a share (\\\\server) or a slash after a space or a quote. A
# file's path ends at its extension; a folder's runs to the end of its quote or of the line, so a
# folder with a space ("Ana Ruiz") never shows its second half (audit 2026-11-09, B4-01).
_START = r"(?:(?<![\w])[A-Za-z]:[\\/]|\\\\|(?<![\w.:/])/(?=[\w~.]))"
_PATH = re.compile(
    _START + r"(?:[^'\"<>|\n]*?\.[A-Za-z0-9]{1,6}(?=[\s'\",;:)]|$)|[^'\"<>|\n]*)"
)  # to its file's extension when it has one; otherwise to the end of the quote or the line
# A file name in quotes, with a document's extension: 'Historia clinica Ana.pdf'.
_QUOTED = re.compile(r"(['\"])([^'\"\n]{1,255}?(\.[A-Za-z0-9]{1,6}))\1")
_WINDOWS = {"ttk": "ttk", "pyside": "qt", "flet": "flet"}


def without_paths(text: str, placeholder: str, names: Iterable[str] = ()) -> str:
    """``text`` with each path, each quoted file name and each of ``names`` (the files and
    folders the person chose) replaced by ``<placeholder>``, the extension kept; the home folder
    first, wherever it appears. A best effort: the message asks to check before sending."""
    home = os.path.expanduser("~")
    if len(home) > 1:
        text = text.replace(home, "/home")
    for name in sorted({n for n in names if len(n) >= 3}, key=len, reverse=True):
        extension = name[name.rfind(".") :] if "." in name[1:] else ""
        text = text.replace(name, f"<{placeholder}>{extension}")
    text = _QUOTED.sub(lambda m: f"{m.group(1)}<{placeholder}>{m.group(3)}{m.group(1)}", text)

    def hidden(match: re.Match[str]) -> str:
        path = match.group(0).rstrip(".,;)")
        tail = match.group(0)[len(path) :]
        name = re.split(r"[\\/]", path)[-1]
        extension = name[name.rfind(".") :] if "." in name[1:] else ""
        return f"<{placeholder}>{extension}{tail}"

    return _PATH.sub(hidden, text)


def window_of(view: object) -> str:
    """Which window is open, from the view's own package: "ttk", "qt" or "flet"."""
    parts = type(view).__module__.split(".")
    return next((_WINDOWS[part] for part in parts if part in _WINDOWS), "")


def details_text(
    catalog: Catalog, version: str, view: object, detail: str, names: Iterable[str] = ()
) -> str:
    window = window_of(view)
    shown = catalog.text(f"gui.app.window_{window}") if window else "?"
    system = f"{platform.system()} {platform.release()}".strip()
    placeholder = catalog.text("gui.app.file_placeholder")
    return catalog.text(
        "gui.app.details_text",
        version=version,
        window=shown,
        system=system,
        detail=without_paths(detail, placeholder, names),
    )
