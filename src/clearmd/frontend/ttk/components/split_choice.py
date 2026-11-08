"""Split's choices on step 1 (features 023, 024): into N parts, every N pages or parts of about N
words, and what to keep. Shown in the results card in place of the images' choice. A number is
committed on Enter, when the field loses the focus, or with its arrows; the presenter refuses a
number out of range and sends the choice again, which the field then shows."""

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

OnSplit = Callable[..., None]  # presenter.choose_split(cut=, parts=, pages=, words=, keep=)
_CUTS = (  # the cut, the words before its number and after it
    ("parts", "gui.split.into", "gui.split.parts"),
    ("pages", "gui.split.every", "gui.split.pages"),
    ("words", "gui.split.words", "gui.split.words_unit"),  # feature 024
)
_STEP = {"words": 1000}  # the arrows of the words' field
_KEEP = (
    ("pdf", "gui.split.keep_pdf"),
    ("markdown", "gui.split.keep_markdown"),
    ("both", "gui.split.keep_both"),
)


class SplitChoice(ttk.Frame):
    """How to Split: the three cuts with their numbers, Keep, the note and the hint."""

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
        self._shown: dict[str, int] = {"parts": 2, "pages": 50, "words": 30_000}
        heading = ttk.Frame(self, style="TFrame")  # the title, and Keep at its right (as Qt)
        heading.pack(fill="x")
        title = ttk.Label(heading, font=fonts["strong"])
        title.pack(side="left")
        label(title, "gui.split.title")
        # The three cuts on one row, or wrapped two and one when the card is too narrow.
        self._row = ttk.Frame(self, style="TFrame")
        self._row.pack(fill="x", pady=(HALF, 0))  # tight: the list keeps a row at 720 px
        self._row.bind("<Configure>", lambda event: self._reflow(event.width))
        self._wrapped: bool | None = None
        self.cut = tk.StringVar(master=self, value="parts")
        self.cuts: dict[str, ttk.Radiobutton] = {}
        self.numbers: dict[str, ttk.Spinbox] = {}
        self._groups: list[ttk.Frame] = []
        for name, before, after in _CUTS:
            group = ttk.Frame(self._row, style="TFrame")
            radio = ttk.Radiobutton(
                group, variable=self.cut, value=name, command=partial(on_split, cut=name)
            )
            radio.pack(side="left")
            label(radio, before)
            low, high = RANGES[f"split_{name}"]
            number = ttk.Spinbox(
                group, from_=low, to=high, increment=_STEP.get(name, 1),
                width=6 if name == "words" else 4, justify="right",
                command=partial(self._commit, name),
            )  # fmt: skip
            number.pack(side="left", padx=(SPACE, 0))
            for event in ("<Return>", "<KP_Enter>", "<FocusOut>"):
                number.bind(event, lambda _event, n=name: self._commit(n))
            unit = ttk.Label(group)
            unit.pack(side="left", padx=(HALF, 0))
            label(unit, after)
            self.cuts[name] = radio
            self.numbers[name] = number
            self._groups.append(group)
        self._reflow(0)
        keep = ttk.Frame(heading, style="TFrame")
        keep.pack(side="right")
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
        self.note.pack(fill="x", pady=(HALF, 0))
        label(self.note, "gui.split.note")
        self.hint = ttk.Label(self, style=MUTED, anchor="w", justify="left")  # 024: about
        self.hint.pack(fill="x", pady=(HALF, 0))
        label(self.hint, "gui.split.hint")
        self.bind("<Configure>", self._wrap_texts, add="+")

    @property
    def controls(self) -> list[ttk.Widget]:
        """Enabled and disabled with the output's choice."""
        return [*self.cuts.values(), *self.numbers.values(), *self.keeps.values()]

    def show(self, choice: OutputChoice) -> None:
        self.cut.set(choice.split_cut)
        self.keep.set(choice.split_keep)
        self._shown = {
            "parts": choice.split_parts, "pages": choice.split_pages, "words": choice.split_words,
        }  # fmt: skip
        for name, value in self._shown.items():
            self._set_number(name, value)

    def _reflow(self, width: int) -> None:
        """One row when the three cuts fit ``width`` (0: before it is known), else two and one."""
        needed = sum(group.winfo_reqwidth() for group in self._groups) + 2 * GAP
        wrapped = width > 0 and needed > width
        if wrapped == self._wrapped:
            return
        self._wrapped = wrapped
        for index, group in enumerate(self._groups):
            row, column = (index // 2, index % 2) if wrapped else (0, index)
            padx = (0 if column == 0 else GAP, 0)
            pady = (0 if row == 0 else SPACE, 0)
            span = 2 if wrapped and index == 2 else 1  # the third alone: its own width, no gap
            group.grid(row=row, column=column, columnspan=span, sticky="w", padx=padx, pady=pady)

    def _wrap_texts(self, event: Any) -> None:
        if event.widget is self:
            for text in (self.note, self.hint):
                text.configure(wraplength=max(event.width, 200))

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
