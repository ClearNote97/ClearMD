"""The keyboard and the mouse of a file list (UX §6, feature 007): the checkboxes and the keys that
move, check and select."""

from functools import partial
from tkinter import ttk
from typing import Any

from clearmd.frontend.ttk.visuals import marks


class ListKeys:
    """Binds a list's keys and clicks, and owns the selection changes they make."""

    def __init__(self, tree: ttk.Treeview, *, checks: bool) -> None:
        self.tree = tree
        self._checks = checks
        tree.bind("<Button-1>", self._clicked)
        # The keyboard too (UX §6): Space checks the row with the focus, Ctrl+A checks all.
        tree.bind("<space>", lambda _event: self.toggle_focused())
        tree.bind("<Control-a>", lambda _event: self._select_all())
        tree.bind("<Control-A>", lambda _event: self._select_all())
        # The arrows move the focus only, so checks add up (a keyboard can check rows 1 and 3);
        # with Shift they check the rows they pass (adversarial check of 007, C7-7).
        for key, step in (("Up", -1), ("Down", 1)):
            tree.bind(f"<{key}>", partial(self.move, step, False))
            tree.bind(f"<Shift-{key}>", partial(self.move, step, True))

    def toggle(self, item: str) -> None:
        self.tree.selection_toggle(item)

    def toggle_all(self) -> None:
        children = self.tree.get_children()
        if children and len(self.tree.selection()) == len(children):
            self.tree.selection_remove(*children)
        else:
            self.tree.selection_set(children)

    def move(self, step: int, check: bool, _event: object = None) -> str:
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

    def toggle_focused(self) -> str:
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
        on_box = self._checks and column == "#0" and event.x <= marks.CHECK_ZONE + 16
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
