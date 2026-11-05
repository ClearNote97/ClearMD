"""A numbered list of files with their icons, in a card (ADR-0027): inputs, the plan, the result."""

import tkinter as tk
from collections.abc import Sequence
from dataclasses import dataclass
from functools import partial
from tkinter import ttk
from typing import Any

from PIL import ImageTk

from clearmd.frontend.design.palette import Palette
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
    tag: str = ""  # "warning" draws the row in the warning colour
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
        self._pictures: dict[str, tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]] = {}
        self._header_boxes: dict[str, ImageTk.PhotoImage] = {}
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
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self._sync_boxes(), add="+")
        self.tree.bind("<Button-1>", self._clicked)
        # The keyboard too (UX §6): Space checks the row with the focus, Ctrl+A checks all.
        self.tree.bind("<space>", lambda _event: self._toggle_focused())
        self.tree.bind("<Control-a>", lambda _event: self._select_all())
        self.tree.bind("<Control-A>", lambda _event: self._select_all())
        # The arrows move the focus only, so checks add up (a keyboard can check rows 1 and 3);
        # with Shift they check the rows they pass (adversarial check of 007, C7-7).
        for key, step in (("Up", -1), ("Down", 1)):
            self.tree.bind(f"<{key}>", partial(self._move, step, False))
            self.tree.bind(f"<Shift-{key}>", partial(self._move, step, True))

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
        self._header_boxes = {
            state: ImageTk.PhotoImage(self._box(state, palette), master=self)
            for state in ("off", "on", "some")
            if self.checks
        }
        children = self.tree.get_children()
        selected = [children.index(item) for item in self.tree.selection()]
        focus = children.index(self.tree.focus()) if self.tree.focus() in children else None
        self.show(self._rows)  # the row pictures carry the palette's colour: drawn again
        children = self.tree.get_children()
        self.tree.selection_set([children[i] for i in selected if i < len(children)])
        if focus is not None and focus < len(children):
            self.tree.focus(children[focus])

    # --- Rows ----------------------------------------------------------------------------------

    def show(self, rows: Sequence[ListRow]) -> None:
        items = self.tree.get_children()
        focused = self.tree.focus()
        place = items.index(focused) if focused in items else 0  # kept after the rebuild
        self._rows = tuple(rows)
        self.tree.delete(*self.tree.get_children())
        self._items.clear()
        self._pictures.clear()
        palette = self._palette
        colour = palette.muted if palette else "#5B6672"
        digits = len(str(len(self._rows)))
        for number, row in enumerate(self._rows, start=1):
            icon = marks.icon(row.icon)
            off, on = (
                ImageTk.PhotoImage(
                    marks.numbered(
                        number,
                        icon,
                        colour,
                        digits=digits,
                        check=self._box(state) if self.checks else None,
                    ),
                    master=self,
                )
                for state in ("off", "on")
            )
            item = self.tree.insert(
                "", "end", text=f"  {row.name}", image=off, values=row.values, tags=(row.tag,)
            )
            self._pictures[item] = (off, on)
            self._items[item] = row
        self._sync_boxes()
        if self._rows:
            self.tree.focus(self.tree.get_children()[min(place, len(self._rows) - 1)])
            self.empty.place_forget()
        else:
            self.empty.place(relx=0.5, rely=0.55, anchor="center")

    # --- Selection by checkboxes (feature 007) ------------------------------------------------

    def _box(self, state: str, palette: Palette | None = None) -> Any:
        p = palette or self._palette
        if p is None:
            return marks.checkbox(state, box="#0F766E", border="#5B6672", mark="#FFFFFF")
        return marks.checkbox(state, box=p.accent, border=p.muted, mark=p.on_accent)

    def _sync_boxes(self) -> None:
        """Each row's box shows whether it is selected; the header's, all, none or some."""
        selected = set(self.tree.selection())
        for item, (off, on) in self._pictures.items():
            if self.tree.exists(item):
                self.tree.item(item, image=on if item in selected else off)
        if self._header_boxes:
            total = len(self._pictures)
            state = "off" if not selected else "on" if len(selected) == total else "some"
            self.tree.heading("#0", image=self._header_boxes[state])

    def checked(self) -> list[bool]:
        """Whether each row's box is checked (for tests)."""
        return [str(self.tree.item(item, "image")[0]) == str(self._pictures[item][1])
                for item in self.tree.get_children()]  # fmt: skip

    def toggle(self, item: str) -> None:
        self.tree.selection_toggle(item)

    def toggle_all(self) -> None:
        children = self.tree.get_children()
        if children and len(self.tree.selection()) == len(children):
            self.tree.selection_remove(*children)
        else:
            self.tree.selection_set(children)

    def _move(self, step: int, check: bool, _event: object = None) -> str:
        items = self.tree.get_children()
        if not items:
            return "break"
        focused = self.tree.focus()
        here = items.index(focused) if focused in items else -1
        target = items[min(max(here + step, 0), len(items) - 1)]
        if check:
            if focused in items:
                self.tree.selection_add(focused)
            self.tree.selection_add(target)
        self.tree.focus(target)
        self.tree.see(target)
        return "break"

    def _toggle_focused(self) -> str:
        focused = self.tree.focus()
        if focused:
            self.toggle(focused)
        return "break"

    def _select_all(self) -> str:
        self.tree.selection_set(self.tree.get_children())
        return "break"

    def clear_selection(self) -> None:
        self.tree.selection_remove(*self.tree.selection())

    def _clicked(self, event: Any) -> str | None:
        """A box toggles its row (or, in the header, every row); empty space clears."""
        region = self.tree.identify_region(event.x, event.y)
        column = self.tree.identify_column(event.x)
        on_box = self.checks and column == "#0" and event.x <= marks.CHECK_ZONE + 16
        if region == "heading" and on_box:
            self.toggle_all()
            return "break"
        row = self.tree.identify_row(event.y)
        if not row:
            if region in {"nothing", ""}:
                self.clear_selection()
            return None
        if on_box:
            self.toggle(row)
            self.tree.focus(row)
            return "break"
        return None

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
