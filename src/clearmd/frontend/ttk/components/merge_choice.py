"""Merge's choice on step 1 (feature 026): into one Markdown or one PDF (PDF files only). Shown in
the results card in place of the images' choice, as Split's block is for Split."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from functools import partial
from tkinter import ttk
from typing import Any

from clearmd.frontend.design.metrics import GAP, HALF
from clearmd.frontend.presenter.models import OutputChoice
from clearmd.frontend.ttk.components.split_choice import OnSplit
from clearmd.frontend.ttk.visuals.style_names import MUTED

_INTO = (("markdown", "gui.merge.markdown"), ("pdf", "gui.merge.pdf"))


class MergeChoice(ttk.Frame):
    """How to Merge: Into one Markdown or one PDF, and the note."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        fonts: dict[str, tkfont.Font],
        on_split: OnSplit,  # presenter.choose_split(into=...): the tools' one choice intent
        label: Callable[[Any, str], None],
    ) -> None:
        super().__init__(parent, style="TFrame")
        title = ttk.Label(self, font=fonts["strong"])
        title.pack(anchor="w")
        label(title, "gui.merge.title")
        row = ttk.Frame(self, style="TFrame")
        row.pack(fill="x", pady=(HALF, 0))
        into = ttk.Label(row, font=fonts["strong"])
        into.pack(side="left")
        label(into, "gui.merge.into")
        self.into = tk.StringVar(master=self, value="markdown")
        self.choices: dict[str, ttk.Radiobutton] = {}
        for value, key in _INTO:
            button = ttk.Radiobutton(
                row, variable=self.into, value=value, command=partial(on_split, into=value)
            )
            button.pack(side="left", padx=(GAP, 0))
            label(button, key)
            self.choices[value] = button
        self.note = ttk.Label(self, style=MUTED, anchor="w", justify="left")
        self.note.pack(fill="x", pady=(HALF, 0))
        label(self.note, "gui.merge.note")
        self.bind(
            "<Configure>",
            lambda event: self.note.configure(wraplength=max(event.width, 200)),
            add="+",
        )

    @property
    def controls(self) -> list[ttk.Widget]:
        """Enabled and disabled with the output's choice."""
        return list(self.choices.values())

    def show(self, choice: OutputChoice) -> None:
        self.into.set(choice.merge_into)
