"""Closing the window while a task runs (feature 038, audit v2 F1-01): asked once, and only then.
Keep Working is the default (Enter, Esc, the dialog's own close); Close cancels and waits, as
closing did before. Cancel in the action bar never asks."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from tkinter import ttk

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.ttk.components.dialog import Dialog
from clearmd.frontend.ttk.visuals.style_names import PRIMARY, SOFT
from clearmd.i18n import Catalog


class ConfirmCloseDialog(Dialog):
    """``on_confirm`` runs when Close is chosen; any other way out keeps working."""

    def __init__(
        self,
        parent: tk.Misc,
        catalog: Catalog,
        palette: Palette,
        fonts: dict[str, tkfont.Font],
        on_confirm: Callable[[], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(
            parent,
            title=catalog.text("gui.close.title"),
            palette=palette,
            fonts=fonts,
            on_close=on_close,
            width=480,
        )
        self._on_confirm = on_confirm
        ttk.Label(
            self.body, text=catalog.text("gui.close.body"), wraplength=420, justify="left"
        ).pack(anchor="w")
        self.keep = ttk.Button(
            self.actions, text=catalog.text("gui.close.keep"), style=PRIMARY, command=self.close
        )
        self.keep.pack(side="right")
        self.close_button = ttk.Button(
            self.actions, text=catalog.text("gui.close.close"), style=SOFT, command=self.confirm
        )
        self.close_button.pack(side="right", padx=(0, SPACE))
        self.bind("<Return>", lambda _event: self._enter())

    def _enter(self) -> None:
        """Enter runs Close only when it has the focus; else Keep Working (the default)."""
        if self.focus_get() is self.close_button:
            self.confirm()
        else:
            self.close()

    def confirm(self) -> None:
        self.close()
        self._on_confirm()
