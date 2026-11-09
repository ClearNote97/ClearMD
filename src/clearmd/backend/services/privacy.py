"""Hiding where a person's files are (audit v3, B2-03): every technical detail ClearMD keeps or
shows — the summary's "Technical Detail", "Copy Details" — has its paths and file names replaced
by ``<file>.ext``, because names and folders belong to people."""

import os
import re
from collections.abc import Iterable

# A path starts at a drive (C:\\), a share (\\\\server) or a slash after a space or a quote. A
# file's path ends at its extension; a folder's runs to the end of its quote or of the line, so a
# folder with a space ("Ana Ruiz") never shows its second half (audit 2026-11-09, B4-01).
_START = r"(?:(?<![\w])[A-Za-z]:[\\/]|\\\\|(?<![^\s'\"(=])/(?=[\w~.]))"
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
