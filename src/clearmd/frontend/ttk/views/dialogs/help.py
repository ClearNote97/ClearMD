"""The help dialog: how to use it, what it converts, where results go, privacy (UX §4)."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from tkinter import ttk

from clearmd.frontend.design.metrics import GAP, HALF
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.ttk.components.dialog import Dialog
from clearmd.frontend.ttk.visuals.style_names import HINT, PRIMARY
from clearmd.i18n import Catalog

_HELP_SECTIONS = ("how", "formats", "where", "keyboard", "privacy", "language")


HELP_WIDTH = 720  # wide and short: it fits a 1366 × 768 screen with its taskbar


def help_dialog(
    parent: tk.Misc,
    catalog: Catalog,
    palette: Palette,
    fonts: dict[str, tkfont.Font],
    on_close: Callable[[], None],
    version: str = "",
) -> Dialog:
    """How to use it, what it converts, where results go, privacy, the language (UX §4); the
    version at the foot (feature 007)."""
    dialog = Dialog(
        parent,
        title=catalog.text("gui.help.title"),
        palette=palette,
        fonts=fonts,
        on_close=on_close,
    )
    for index, section in enumerate(_HELP_SECTIONS):
        title = ttk.Label(dialog.body, text=catalog.text(f"gui.help.{section}_title"))
        title.configure(font=fonts["strong"])
        title.pack(anchor="w", pady=(0 if index == 0 else GAP, 0))
        text = ttk.Label(
            dialog.body,
            text=catalog.text(f"gui.help.{section}"),
            wraplength=HELP_WIDTH,
            justify="left",
        )
        text.pack(anchor="w", pady=(HALF, 0))
    if version:
        shown = catalog.text("gui.help.version", version=version)
        ttk.Label(dialog.actions, text=shown, style=HINT).pack(side="left")
    close = ttk.Button(
        dialog.actions, text=catalog.text("gui.help.close"), style=PRIMARY, command=dialog.close
    )
    close.pack(side="right")
    dialog.bind("<Return>", lambda _event: dialog.close())
    return dialog
