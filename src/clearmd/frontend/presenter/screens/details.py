"""What "Copy Details" copies after an unexpected error (doubts board 2026-11-09, D3): the version,
the window, the system and the error, with every path and file name it can find replaced by
``<file>.ext`` by the backend's ``without_paths``, because a report goes to a public page."""

import platform
from collections.abc import Iterable

from clearmd.backend.api import without_paths
from clearmd.i18n import Catalog

_WINDOWS = {"ttk": "ttk", "pyside": "qt", "flet": "flet"}


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
