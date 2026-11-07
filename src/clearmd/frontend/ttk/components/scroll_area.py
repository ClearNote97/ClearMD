"""A frame that scrolls when it is taller than the room it is given (feature 023: Settings grew
past a 720 px window with Split's group). The wheel scrolls it while the pointer is over it."""

import tkinter as tk
from tkinter import ttk
from typing import Any

from clearmd.frontend.design.metrics import SPACE

_WHEEL = ("<MouseWheel>", "<Button-4>", "<Button-5>")


class ScrollArea(ttk.Frame):
    """``inner`` is the frame to fill; ``fit(limit)`` shows all of it, or ``limit`` pixels of it
    with a scroll bar."""

    def __init__(self, parent: tk.Misc, *, ground: str) -> None:
        super().__init__(parent, style="TFrame")
        self._canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0, background=ground)
        self._canvas.pack(side="left", fill="both", expand=True)
        self._bar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._bar.set)
        self.inner = ttk.Frame(self._canvas, style="TFrame")
        self._window = self._canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda _event: self._resized())
        self._canvas.bind(
            "<Configure>", lambda event: self._canvas.itemconfigure(self._window, width=event.width)
        )
        for sequence in _WHEEL:  # the wheel is the whole application's: let go on destroy
            self.bind_all(sequence, self._wheel, add="+")
        self.bind("<Destroy>", self._destroyed, add="+")

    @property
    def scrolls(self) -> bool:
        return bool(self._bar.winfo_manager())

    def fit(self, limit: int) -> None:
        """As tall as its content, at most ``limit``: then the bar shows."""
        self.update_idletasks()
        needed = self.inner.winfo_reqheight()
        self._canvas.configure(width=self.inner.winfo_reqwidth(), height=min(needed, limit))
        if needed > limit:
            self._bar.pack(side="right", fill="y", padx=(SPACE, 0), before=self._canvas)
        else:
            self._bar.pack_forget()

    def _destroyed(self, event: Any) -> None:
        if event.widget is self:
            for sequence in _WHEEL:
                self.unbind_all(sequence)

    def _resized(self) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _wheel(self, event: Any) -> None:
        if not self.scrolls or not self._over(event):
            return
        if event.num == 4 or getattr(event, "delta", 0) > 0:
            self._canvas.yview_scroll(-1, "units")
        else:
            self._canvas.yview_scroll(1, "units")

    def _over(self, event: Any) -> bool:
        widget = event.widget
        while isinstance(widget, tk.Misc):
            if widget is self:
                return True
            widget = widget.master
        return False
