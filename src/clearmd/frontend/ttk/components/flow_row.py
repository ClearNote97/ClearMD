"""A row of controls that wraps when the room is too narrow (feature 028: Review's three answers
did not fit at 1080 px in Spanish). On one row while they fit; else ``wrapped`` per row."""

import tkinter as tk
from tkinter import ttk
from typing import Any

from clearmd.frontend.design.metrics import GAP, HALF


class FlowRow(ttk.Frame):
    """Its children, added with ``add``, laid out on the grid: on one row, or wrapped."""

    def __init__(self, parent: tk.Misc, *, wrapped: int = 1, style: str = "TFrame") -> None:
        super().__init__(parent, style=style)
        self._per_row = wrapped
        self._items: list[ttk.Widget] = []
        self._wrapped: bool | None = None
        self.bind("<Configure>", lambda event: self.reflow(event.width))

    def add(self, widget: ttk.Widget) -> None:
        self._items.append(widget)
        self._wrapped = None
        self.reflow(self.winfo_width())

    def refresh(self) -> None:
        """Lay out again once the texts have changed (another language): after Tk measures."""
        self._wrapped = None
        self.after_idle(lambda: self.reflow(self.winfo_width()))

    @property
    def wrapped(self) -> bool:
        return bool(self._wrapped)

    def reflow(self, width: int) -> None:
        """One row when the items fit ``width`` (1 or less: not yet known), else wrapped."""
        needed = sum(item.winfo_reqwidth() for item in self._items)
        needed += GAP * max(len(self._items) - 1, 0)
        wrapped = width > 1 and needed > width
        if wrapped == self._wrapped:
            return
        self._wrapped = wrapped
        per_row = self._per_row if wrapped else len(self._items)
        for index, item in enumerate(self._items):
            row, column = divmod(index, max(per_row, 1))
            options: dict[str, Any] = {
                "padx": (0 if column == 0 else GAP, 0),
                "pady": (0 if row == 0 else HALF, 0),
            }
            item.grid(row=row, column=column, sticky="w", **options)
