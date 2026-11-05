"""The welcome dialog: the three steps and "Don't show again" (UX §4; AC-14)."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from tkinter import ttk

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.ttk.components.dialog import Dialog
from clearmd.frontend.ttk.visuals.style_names import CHECK_ON_PAGE, MUTED, PRIMARY
from clearmd.i18n import Catalog


class WelcomeDialog(Dialog):
    """The three steps and "Don't show again" (UX §4; AC-14)."""

    def __init__(
        self,
        parent: tk.Misc,
        catalog: Catalog,
        palette: Palette,
        fonts: dict[str, tkfont.Font],
        steps: tuple[str, ...],
        on_done: Callable[[bool], None],
    ) -> None:
        self.dont_show = tk.BooleanVar(value=False)
        super().__init__(
            parent,
            title=catalog.text("gui.welcome.title"),
            palette=palette,
            fonts=fonts,
            on_close=lambda: on_done(not self.dont_show.get()),
            width=560,
        )
        ttk.Label(self.body, text=catalog.text("gui.welcome.intro")).pack(anchor="w")
        for step in steps:
            line = ttk.Label(self.body, text=step, font=fonts["strong"])
            line.pack(anchor="w", pady=(SPACE, 0))
        language = ttk.Label(
            self.body, text=catalog.text("gui.help.language"), style=MUTED, wraplength=480
        )
        language.pack(anchor="w", pady=(GAP, 0))
        check = ttk.Checkbutton(
            self.actions, text=catalog.text("gui.welcome.dont_show"), variable=self.dont_show
        )
        check.configure(style=CHECK_ON_PAGE)
        check.pack(side="left")
        start = ttk.Button(
            self.actions, text=catalog.text("gui.welcome.start"), style=PRIMARY, command=self.close
        )
        start.pack(side="right")
        self.bind("<Return>", lambda _event: self.close())
