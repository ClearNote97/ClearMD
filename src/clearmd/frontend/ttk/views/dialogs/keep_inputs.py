"""The "What Next?" dialog (features 007, 032): keep the chosen files, start empty, or go back
Home to choose another tool (the files are kept)."""

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
    """ "What Next?": Keep Them, Start Empty or Go Back Home (asked every time; 007, 032).
    ``on_answer`` receives "keep", "clear" or "home"."""

    def __init__(
        self,
        parent: tk.Misc,
        catalog: Catalog,
        palette: Palette,
        fonts: dict[str, tkfont.Font],
        on_answer: Callable[[str], None],
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
            command=lambda: self.answer("keep"),
        )  # fmt: skip
        self.keep.pack(side="right")
        self.clear = ttk.Button(
            self.actions, text=catalog.text("gui.more.clear"), style=SOFT,
            command=lambda: self.answer("clear"),
        )  # fmt: skip
        self.clear.pack(side="right", padx=(0, SPACE))
        self.home = ttk.Button(
            self.actions, text=catalog.text("gui.more.home"), style=SOFT,
            command=lambda: self.answer("home"),
        )  # fmt: skip
        self.home.pack(side="left")  # apart, as Settings' Restore Defaults: another way out
        self.bind("<Return>", lambda _event: self._enter())

    def _enter(self) -> None:
        """Enter runs the button with the focus; elsewhere, the default (keep them)."""
        focused = self.focus_get()
        choice = "clear" if focused is self.clear else "home" if focused is self.home else "keep"
        self.answer(choice)

    def answer(self, choice: str | bool) -> None:
        """The answer: "keep", "clear" or "home" (True and False: keep or clear, as before)."""
        if isinstance(choice, bool):
            choice = "keep" if choice else "clear"
        self.close()
        self._on_answer(choice)
