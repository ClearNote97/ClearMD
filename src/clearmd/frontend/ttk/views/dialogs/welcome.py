"""The welcome dialog: the three steps, the language at once, and "Don't show again" (UX §4;
AC-14; audit v3 F4-05). "English" and "Español", each in its own language, switch the window's
language while the Welcome is open: it speaks the new one at once."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from functools import partial
from tkinter import ttk
from typing import Any

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.ttk.components.dialog import Dialog
from clearmd.frontend.ttk.visuals.style_names import CHECK_ON_PAGE, MUTED, PRIMARY, SOFT_ON_CARD
from clearmd.i18n import Catalog

LANGUAGES = ("en", "es")


class WelcomeDialog(Dialog):
    """The three steps, the language's two buttons and "Don't show again" (UX §4; AC-14)."""

    def __init__(
        self,
        parent: tk.Misc,
        catalog: Catalog,
        palette: Palette,
        fonts: dict[str, tkfont.Font],
        steps: tuple[str, ...],
        on_done: Callable[[bool], None],
        on_language: Callable[[str], None] = lambda _language: None,
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
        self._texts: list[tuple[Any, str]] = []  # a widget and its catalog key
        self._label(ttk.Label(self.body), "gui.welcome.intro").pack(anchor="w")
        self.steps = [ttk.Label(self.body, text=step, font=fonts["strong"]) for step in steps]
        for number, line in enumerate(self.steps, start=1):
            line.pack(anchor="w", pady=(SPACE, 0))
            if len(self.steps) == 3:  # the presenter's three steps: their keys, for a new language
                self._texts.append((line, f"gui.welcome.step{number}"))
        language = ttk.Label(self.body, style=MUTED, wraplength=480)
        self._label(language, "gui.help.language").pack(anchor="w", pady=(GAP, 0))
        row = ttk.Frame(self.body, style="TFrame")
        row.pack(anchor="w", pady=(SPACE, 0))
        self.languages: dict[str, ttk.Button] = {}
        for code in LANGUAGES:  # each named in its own language, whatever the current one
            button = ttk.Button(
                row,
                text=catalog.text(f"gui.welcome.language_{code}"),
                style=SOFT_ON_CARD,
                command=partial(on_language, code),
            )
            button.pack(side="left", padx=(0 if code == LANGUAGES[0] else SPACE, 0))
            self.languages[code] = button
        check = ttk.Checkbutton(self.actions, variable=self.dont_show, style=CHECK_ON_PAGE)
        self._label(check, "gui.welcome.dont_show").pack(side="left")
        start = ttk.Button(self.actions, style=PRIMARY, command=self.close)
        self._label(start, "gui.welcome.start").pack(side="right")
        self.apply_language(catalog)
        self.bind("<Return>", lambda _event: self._enter())

    def _label(self, widget: Any, key: str) -> Any:
        self._texts.append((widget, key))
        return widget

    def _enter(self) -> None:
        """Enter on a language button chooses it (UX §6); elsewhere it starts."""
        focused = self.focus_get()
        if focused in self.languages.values():
            focused.invoke()  # type: ignore[union-attr]
        else:
            self.close()

    def apply_language(self, catalog: Catalog) -> None:
        """The Welcome speaks the window's language, even after a switch while it is open."""
        title = catalog.text("gui.welcome.title")
        self.title(title)
        self.heading.configure(text=title)
        for widget, key in self._texts:
            widget.configure(text=catalog.text(key))
