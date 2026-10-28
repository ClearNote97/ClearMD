"""A numbered list of files with their icons, in a card (ADR-0027): inputs, the plan, the result."""

import tkinter as tk
from collections.abc import Sequence
from dataclasses import dataclass
from tkinter import ttk
from typing import Any

from PIL import ImageTk

from clearmd.frontend.ttk import art
from clearmd.frontend.ttk.brand import CARD, MUTED, Palette


@dataclass(frozen=True)
class Column:
    key: str  # the catalog key of its heading
    width: int
    stretch: bool = False


@dataclass(frozen=True)
class ListRow:
    icon: str
    name: str
    values: tuple[str, ...]  # one per extra column
    tag: str = ""  # "warning" draws the row in the warning colour
    payload: Any = None  # what the row stands for (a path), returned by ``selected``


class FileList(ttk.Frame):
    """``#`` and icon, the name, then the extra columns; a message in place of an empty list."""

    def __init__(
        self, parent: tk.Misc, *, name_heading: str, columns: Sequence[Column], height: int = 6
    ) -> None:
        super().__init__(parent, style=CARD, padding=8)
        self._columns = tuple(columns)
        self._name_heading = name_heading
        self._palette: Palette | None = None
        self._rows: tuple[ListRow, ...] = ()
        self._items: dict[str, ListRow] = {}
        self._pictures: list[ImageTk.PhotoImage] = []
        keys = [f"c{i}" for i in range(len(self._columns))]
        self.tree = ttk.Treeview(self, columns=keys, height=height, selectmode="extended")
        self.tree.column("#0", width=300, stretch=False)  # the extra columns take what is left
        for key, column in zip(keys, self._columns, strict=True):
            self.tree.column(key, width=column.width, stretch=column.stretch, anchor="w")
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")
        self.empty = ttk.Label(self.tree, style=MUTED, anchor="center", justify="center")

    # --- Texts and colours ------------------------------------------------------------------

    def apply_headings(self, name: str, others: Sequence[str], empty: str) -> None:
        self.tree.heading("#0", text=name, anchor="w")
        for index, text in enumerate(others):
            self.tree.heading(f"c{index}", text=text, anchor="w")
        self.empty.configure(text=empty)

    def apply_palette(self, palette: Palette) -> None:
        self._palette = palette
        self.tree.tag_configure("warning", foreground=palette.warning)
        self.show(self._rows)

    # --- Rows ----------------------------------------------------------------------------------

    def show(self, rows: Sequence[ListRow]) -> None:
        self._rows = tuple(rows)
        self.tree.delete(*self.tree.get_children())
        self._items.clear()
        self._pictures.clear()
        colour = self._palette.muted if self._palette else "#5B6672"
        digits = len(str(len(self._rows)))
        for number, row in enumerate(self._rows, start=1):
            picture = ImageTk.PhotoImage(
                art.numbered(number, art.icon(row.icon), colour, digits=digits), master=self
            )
            self._pictures.append(picture)
            item = self.tree.insert(
                "", "end", text=f"  {row.name}", image=picture, values=row.values, tags=(row.tag,)
            )
            self._items[item] = row
        if self._rows:
            self.empty.place_forget()
        else:
            self.empty.place(relx=0.5, rely=0.55, anchor="center")

    def names(self) -> list[str]:
        """The names as listed (for tests)."""
        return [self._items[item].name for item in self.tree.get_children()]

    def current(self) -> ListRow | None:
        """The row with the keyboard focus or the first selected one."""
        chosen = self.tree.selection() or ((self.tree.focus(),) if self.tree.focus() else ())
        return self._items.get(chosen[0]) if chosen else None

    def select_first(self) -> None:
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])
            self.tree.focus(children[0])

    def selected(self) -> list[Any]:
        return [self._items[item].payload for item in self.tree.selection() if item in self._items]
