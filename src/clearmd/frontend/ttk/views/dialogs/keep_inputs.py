"""The "Convert more" dialog: keep the chosen files or start empty (feature 007)."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from tkinter import ttk

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.ttk.components.dialog import Dialog
from clearmd.frontend.ttk.visuals.style_names import MUTED, PRIMARY, SOFT
from clearmd.i18n import Catalog


class KeepInputsDialog(Dialog):
    """ "Convert more": keep the chosen files, or start empty (asked every time, feature 007)."""

    def __init__(
        self,
        parent: tk.Misc,
        catalog: Catalog,
        palette: Palette,
        fonts: dict[str, tkfont.Font],
        on_answer: Callable[[bool], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(
            parent,
            title=catalog.text("gui.more.title"),
            palette=palette,
            fonts=fonts,
            on_close=on_close,
            width=480,
        )
        self._on_answer = on_answer
        ttk.Label(self.body, text=catalog.text("gui.more.question"), font=fonts["strong"]).pack(
            anchor="w"
        )
        explanation = ttk.Label(
            self.body, text=catalog.text("gui.more.explain"), style=MUTED, wraplength=400
        )
        explanation.pack(anchor="w", pady=(SPACE, 0))
        self.keep = ttk.Button(
            self.actions, text=catalog.text("gui.more.keep"), style=PRIMARY,
            command=lambda: self.answer(True),
        )  # fmt: skip
        self.keep.pack(side="right")
        self.clear = ttk.Button(
            self.actions, text=catalog.text("gui.more.clear"), style=SOFT,
            command=lambda: self.answer(False),
        )  # fmt: skip
        self.clear.pack(side="right", padx=(0, SPACE))
        self.bind("<Return>", lambda _event: self._enter())

    def _enter(self) -> None:
        """Enter runs the button with the focus; elsewhere, the default (keep them)."""
        focused = self.focus_get()
        self.answer(focused is not self.clear)

    def answer(self, keep: bool) -> None:
        self.close()
        self._on_answer(keep)
