"""What "Copy Details" copies after an unexpected error (doubts board 2026-11-09, D3): the version,
the window, the system and the error, with every path replaced by ``<file>.ext``, because a
report goes to a public page and paths carry people's and documents' names."""

import os
import platform
import re

from clearmd.i18n import Catalog

# A path starts at a drive (C:\), a share (\\server) or a slash after a space or a quote. With
# spaces in it, it ends at its file's extension; without, at the first space (a folder).
_START = r"(?:(?<![\w])[A-Za-z]:[\\/]|\\\\|(?<![\w.:/])/)"
_PATH = re.compile(_START + r"(?:[^'\"<>|\n]*?\.[A-Za-z0-9]{1,6}(?=[\s'\",;:)]|$)|[^\s'\"<>|]*)")
_WINDOWS = {"ttk": "ttk", "pyside": "qt", "flet": "flet"}


def without_paths(text: str, placeholder: str) -> str:
    """``text`` with each path replaced by ``<placeholder>`` and the path's extension kept; the
    home folder first, wherever it appears."""
    home = os.path.expanduser("~")
    if len(home) > 1:
        text = text.replace(home, "/home")

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


def details_text(catalog: Catalog, version: str, view: object, detail: str) -> str:
    window = window_of(view)
    shown = catalog.text(f"gui.app.window_{window}") if window else "?"
    system = f"{platform.system()} {platform.release()}".strip()
    placeholder = catalog.text("gui.app.file_placeholder")
    return catalog.text(
        "gui.app.details_text",
        version=version,
        window=shown,
        system=system,
        detail=without_paths(detail, placeholder),
    )
