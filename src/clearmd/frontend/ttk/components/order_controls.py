"""Merge's order on step 1 (feature 032): Move Up and Move Down next to Remove Selected, acting on
the selected row, and the line under the list that says the documents are merged in this order.
Shown only in Merge; each button enabled from the selected row's ``up`` and ``down``."""

import tkinter as tk
from collections.abc import Callable
from functools import partial
from pathlib import Path
from tkinter import ttk
from typing import Any

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.presenter.models import InputRow
from clearmd.frontend.ttk.components.file_list import FileList
from clearmd.frontend.ttk.visuals.style_names import HINT, LINK
from clearmd.i18n import Catalog


class OrderControls:
    """The two buttons (in ``editing``, the row of the list's links) and the hint line."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        files: FileList,
        editing: ttk.Frame,
        on_move: Callable[[Path, int], None],
        label: Callable[[Any, str], None],
    ) -> None:
        self._files = files
        self._editing = editing
        self._on_move = on_move
        self._moves: dict[Path, tuple[bool, bool]] = {}
        self._merging = False
        self._moved: Path | None = None  # selected again once the list comes back
        self.up = ttk.Button(editing, style=LINK, command=lambda: self._move(-1))
        self.down = ttk.Button(editing, style=LINK, command=lambda: self._move(+1))
        self.hint = ttk.Label(parent, style=HINT, anchor="w")
        label(self.hint, "gui.main.order_hint")
        files.tree.bind("<<TreeviewSelect>>", lambda _event: self._enable(), add="+")
        for key, offset in (("<Alt-Up>", -1), ("<Alt-Down>", +1)):  # the keyboard's way too
            files.tree.bind(key, partial(self._key, offset))

    def apply_language(self, catalog: Catalog) -> None:
        """The arrows the hint speaks of, before each button's words."""
        self.up.configure(text=f"▲ {catalog.text('gui.main.move_up')}")
        self.down.configure(text=f"▼ {catalog.text('gui.main.move_down')}")

    def show(self, rows: tuple[InputRow, ...], *, merging: bool) -> None:
        """The rows as listed, and whether the tool is Merge (the only one with an order)."""
        self._moves = {row.path: (row.up, row.down) for row in rows}
        self._merging = merging
        for widget in (self.up, self.down, self.hint):
            widget.pack_forget()
        if merging:
            self.up.pack(side="left", padx=(SPACE, 0))
            self.down.pack(side="left", padx=(SPACE, 0))
            if len(rows) > 1:
                self.hint.pack(side="bottom", fill="x", after=self._editing)
        paths = [row.path for row in rows]
        if self._moved in paths:  # the moved row stays selected, in its new place
            tree = self._files.tree
            item = tree.get_children()[paths.index(self._moved)]
            tree.selection_set(item)
            tree.focus(item)
            tree.see(item)
        self._moved = None
        self._enable()

    def _chosen(self) -> Path | None:
        chosen = self._files.selected()
        return chosen[0] if len(chosen) == 1 and chosen[0] in self._moves else None

    def _enable(self) -> None:
        path = self._chosen()
        up, down = self._moves.get(path, (False, False)) if path is not None else (False, False)
        for button, allowed in ((self.up, up), (self.down, down)):
            button.state(["!disabled"] if self._merging and allowed else ["disabled"])

    def _key(self, offset: int, _event: object) -> str:
        self._move(offset)
        return "break"

    def _move(self, offset: int) -> None:
        path = self._chosen()
        if path is None or not self._merging:
            return
        if not self._moves[path][0 if offset < 0 else 1]:
            return
        self._moved = path
        self._on_move(path, offset)
