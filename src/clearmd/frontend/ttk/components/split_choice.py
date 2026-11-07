"""Split's choices on step 1 (feature 023): into N parts or every N pages, and what to keep.
Shown in the results card in place of the images' choice. A number is committed on Enter, when
the field loses the focus, or with its arrows; the presenter refuses a number out of range and
sends the choice again, which the field then shows."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from functools import partial
from tkinter import ttk
from typing import Any

from clearmd.backend.schemas.settings import RANGES
from clearmd.frontend.design.metrics import GAP, HALF, SPACE
from clearmd.frontend.presenter.models import OutputChoice
from clearmd.frontend.ttk.visuals.style_names import MUTED

OnSplit = Callable[..., None]  # presenter.choose_split(cut=..., parts=..., pages=..., keep=...)
_KEEP = (
    ("pdf", "gui.split.keep_pdf"),
    ("markdown", "gui.split.keep_markdown"),
    ("both", "gui.split.keep_both"),
)


class SplitChoice(ttk.Frame):
    """How to Split: the cut with its number, Keep, and the note."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        fonts: dict[str, tkfont.Font],
        on_split: OnSplit,
        label: Callable[[Any, str], None],
    ) -> None:
        super().__init__(parent, style="TFrame")
        self._on_split = on_split
        self._shown: dict[str, int] = {"parts": 2, "pages": 50}
        cut = ttk.Frame(self, style="TFrame")  # the title, and the cut on its row
        cut.pack(fill="x")
        title = ttk.Label(cut, font=fonts["strong"])
        title.pack(side="left")
        label(title, "gui.split.title")
        self.cut = tk.StringVar(master=self, value="parts")
        self.cuts: dict[str, ttk.Radiobutton] = {}
        self.numbers: dict[str, ttk.Spinbox] = {}
        for name, before, after in (
            ("parts", "gui.split.into", "gui.split.parts"),
            ("pages", "gui.split.every", "gui.split.pages"),
        ):
            radio = ttk.Radiobutton(
                cut, variable=self.cut, value=name, command=partial(on_split, cut=name)
            )
            radio.pack(side="left", padx=(GAP if name == "parts" else 2 * GAP, 0))
            label(radio, before)
            low, high = RANGES[f"split_{name}"]
            number = ttk.Spinbox(
                cut, from_=low, to=high, increment=1, width=6, justify="right",
                command=partial(self._commit, name),
            )  # fmt: skip
            number.pack(side="left", padx=(SPACE, 0))
            for event in ("<Return>", "<KP_Enter>", "<FocusOut>"):
                number.bind(event, lambda _event, n=name: self._commit(n))
            unit = ttk.Label(cut)
            unit.pack(side="left", padx=(HALF, 0))
            label(unit, after)
            self.cuts[name] = radio
            self.numbers[name] = number
        keep = ttk.Frame(self, style="TFrame")
        keep.pack(fill="x", pady=(SPACE, 0))
        keep_title = ttk.Label(keep, font=fonts["strong"])
        keep_title.pack(side="left")
        label(keep_title, "gui.split.keep")
        self.keep = tk.StringVar(master=self, value="both")
        self.keeps: dict[str, ttk.Radiobutton] = {}
        for value, key in _KEEP:
            button = ttk.Radiobutton(
                keep, variable=self.keep, value=value, command=partial(on_split, keep=value)
            )
            button.pack(side="left", padx=(GAP, 0))
            label(button, key)
            self.keeps[value] = button
        self.note = ttk.Label(self, style=MUTED, anchor="w", justify="left")
        self.note.pack(fill="x", pady=(SPACE, 0))
        label(self.note, "gui.split.note")

    @property
    def controls(self) -> list[ttk.Widget]:
        """Enabled and disabled with the output's choice."""
        return [*self.cuts.values(), *self.numbers.values(), *self.keeps.values()]

    def show(self, choice: OutputChoice) -> None:
        self.cut.set(choice.split_cut)
        self.keep.set(choice.split_keep)
        self._shown = {"parts": choice.split_parts, "pages": choice.split_pages}
        for name, value in self._shown.items():
            self._set_number(name, value)

    def _set_number(self, name: str, value: int) -> None:
        field = self.numbers[name]
        disabled = field.instate(["disabled"])
        if disabled:
            field.state(["!disabled"])
        field.delete(0, "end")
        field.insert(0, str(value))
        if disabled:
            field.state(["disabled"])

    def _commit(self, name: str) -> None:
        """The number typed (or stepped) in ``name``'s field, to the presenter; text that is not
        a number shows the stored one again."""
        text = self.numbers[name].get().strip()
        try:
            number = int(text)
        except ValueError:
            self._set_number(name, self._shown[name])
            return
        if number != self._shown[name]:
            self._on_split(**{name: number})
        elif text != str(number):
            self._set_number(name, number)
