"""A numbered list of files with their icons, in a card (ADR-0027): inputs, the plan, the result.
Its scroll bar shows whenever rows are hidden, and its pictures are drawn for the rows on screen
only, so a thousand rows appear at once (feature 035, AC-07)."""

import tkinter as tk
from collections.abc import Sequence
from dataclasses import dataclass
from tkinter import ttk
from typing import Any

from PIL import ImageTk

from clearmd.frontend.design.palette import Palette
from clearmd.frontend.ttk.components.file_list_keys import ListKeys
from clearmd.frontend.ttk.components.row_pictures import RowPictures
from clearmd.frontend.ttk.visuals import marks
from clearmd.frontend.ttk.visuals.style_names import CARD, MUTED


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
    tag: str = ""  # "warning" or "danger" draws the row in that colour (035: a row's tone)
    payload: Any = None  # what the row stands for (a path), returned by ``selected``


class FileList(ttk.Frame):
    """``#`` and icon, the name, then the extra columns; a message in place of an empty list."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        name_heading: str,
        columns: Sequence[Column],
        height: int = 6,
        checks: bool = True,
    ) -> None:
        """``checks``: a checkbox on each row, for a list whose selection does something (Choose's
        Remove selected); a list to read has none: a box promises a choice (feature 014)."""
        super().__init__(parent, style=CARD, padding=8)
        self.checks = checks
        self._columns = tuple(columns)
        self._name_heading = name_heading
        self._palette: Palette | None = None
        self._rows: tuple[ListRow, ...] = ()
        self._items: dict[str, ListRow] = {}
        self._digits = 1
        self._painting: str | None = None
        self._header_boxes: dict[str, ImageTk.PhotoImage] = {}
        keys = [f"c{i}" for i in range(len(self._columns))]
        self.tree = ttk.Treeview(self, columns=keys, height=height, selectmode="extended")
        self.tree.column("#0", width=300, stretch=False)  # the extra columns take what is left
        for key, column in zip(keys, self._columns, strict=True):
            self.tree.column(key, width=column.width, stretch=column.stretch, anchor="w")
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self._scrolled)
        # The bar first: a narrow list keeps it, the rows take what is left (035, AC-07).
        self.scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.pictures = RowPictures(self, self.tree, checks=checks)
        self.empty = ttk.Label(self.tree, style=MUTED, anchor="center", justify="center")
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self._sync_boxes(), add="+")
        self.shortcuts = ListKeys(self.tree, checks=checks)
        self.toggle, self.toggle_all = self.shortcuts.toggle, self.shortcuts.toggle_all
        self.clear_selection = self.shortcuts.clear_selection

    # --- Texts and colours ------------------------------------------------------------------

    def apply_headings(self, name: str, others: Sequence[str], empty: str) -> None:
        name = f"  {name}" if self.checks else name  # after the header's box, if it has one
        self.tree.heading("#0", text=name, anchor="w")
        for index, text in enumerate(others):
            self.tree.heading(f"c{index}", text=text, anchor="w")
        self.empty.configure(text=empty)

    def apply_palette(self, palette: Palette) -> None:
        if palette == self._palette:
            return
        self._palette = palette
        self.tree.tag_configure("warning", foreground=palette.warning)
        self.tree.tag_configure("danger", foreground=palette.danger)
        self._header_boxes = {
            state: ImageTk.PhotoImage(self._box(state, palette), master=self)
            for state in ("off", "on", "some")
            if self.checks
        }
        self.pictures.use(palette)  # the rows stay: only those on screen are painted again
        self._sync_boxes()

    # --- Rows ----------------------------------------------------------------------------------

    def show(self, rows: Sequence[ListRow]) -> None:
        items = self.tree.get_children()
        focused = self.tree.focus()
        place = items.index(focused) if focused in items else 0  # kept after the rebuild
        self._rows = tuple(rows)
        self.tree.delete(*items)
        self._items.clear()
        self.pictures.forget()
        self._digits = len(str(len(self._rows)))
        blank = self.pictures.blank(self._digits)
        for row in self._rows:
            item = self.tree.insert(
                "", "end", text=f"  {row.name}", image=blank, values=row.values, tags=(row.tag,)
            )
            self._items[item] = row
        self._sync_boxes()
        if self._rows:
            self.tree.focus(self.tree.get_children()[min(place, len(self._rows) - 1)])
            self.empty.place_forget()
        else:
            self.empty.place(relx=0.5, rely=0.55, anchor="center")

    def _scrolled(self, first: float, last: float) -> None:
        self.scroll.set(first, last)
        if self._painting is None:  # the rows now on screen get their pictures
            self._painting = self.after_idle(self._paint_visible)

    def _paint_visible(self, *, every: bool = False) -> None:
        self._painting = None
        children = self.tree.get_children()
        if not children:
            return
        first = int(float(self.tree.yview()[0]) * len(children))
        shown = max(self.tree.winfo_height() // 36 + 2, int(str(self.tree.cget("height"))) + 2)
        start, stop = (0, len(children)) if every else (max(first - 1, 0), first + shown)
        selected = set(self.tree.selection())
        rows = self._items
        self.pictures.paint(
            (item, rows[item].icon, index + 1, self._digits, item in selected, rows[item].tag)
            for index, item in enumerate(children[start:stop], start=start)
        )

    # --- Selection by checkboxes (feature 007) ------------------------------------------------

    def _box(self, state: str, palette: Palette | None = None) -> Any:
        p = palette or self._palette
        if p is None:
            return marks.checkbox(state, box="#0F766E", border="#5B6672", mark="#FFFFFF")
        return marks.checkbox(state, box=p.accent, border=p.muted, mark=p.on_accent)

    def _sync_boxes(self) -> None:
        """Each row's box shows whether it is selected; the header's, all, none or some."""
        selected = set(self.tree.selection())
        self._paint_visible()  # only the rows on screen; the others when they come into view
        if self._header_boxes:
            total = len(self._items)
            state = "off" if not selected else "on" if len(selected) == total else "some"
            self.tree.heading("#0", image=self._header_boxes[state])

    def checked(self) -> list[bool]:
        """Whether each row's box is checked (for tests)."""
        self._paint_visible(every=True)
        return [self.pictures.checked(item) for item in self.tree.get_children()]

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
