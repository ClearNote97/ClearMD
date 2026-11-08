"""A frame that scrolls when it is taller than the room it is given: Settings' rows (023) and, in
a small window, step 1's results card (032). The wheel scrolls the one under the pointer; a
control reached with Tab is scrolled into view."""

import tkinter as tk
from tkinter import ttk
from typing import Any, ClassVar

from clearmd.frontend.design.metrics import SPACE

_WHEEL = ("<MouseWheel>", "<Button-4>", "<Button-5>")


class ScrollArea(ttk.Frame):
    """``inner`` is the frame to fill; ``fit(limit)`` shows all of it, or ``limit`` pixels of it
    with a scroll bar. ``fixed_width``: as wide as its content (a dialog), else as its parent."""

    _live: ClassVar[list["ScrollArea"]] = []  # the wheel is the application's: one binding

    def __init__(self, parent: tk.Misc, *, ground: str, fixed_width: bool = True) -> None:
        super().__init__(parent, style="TFrame")
        self._fixed_width = fixed_width
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
        if not ScrollArea._live:
            for sequence in _WHEEL:
                self.bind_all(sequence, ScrollArea._dispatch, add="+")
        ScrollArea._live.append(self)
        self.bind("<Destroy>", self._destroyed, add="+")

    @property
    def scrolls(self) -> bool:
        return bool(self._bar.winfo_manager())

    def set_ground(self, ground: str) -> None:
        self._canvas.configure(background=ground)

    def fit(self, limit: int) -> None:
        """As tall as its content, at most ``limit``: then the bar shows."""
        self.update_idletasks()
        needed = self.inner.winfo_reqheight()
        if self._fixed_width:
            self._canvas.configure(width=self.inner.winfo_reqwidth())
        self._canvas.configure(height=min(needed, limit))
        if needed > limit:
            if not self.scrolls:
                self._bar.pack(side="right", fill="y", padx=(SPACE, 0), before=self._canvas)
        else:
            self._bar.pack_forget()
            self._canvas.yview_moveto(0)

    def see(self, widget: tk.Misc) -> None:
        """Scroll so ``widget`` (inside ``inner``) is in view."""
        if not self.scrolls:
            return
        top = widget.winfo_rooty() - self.inner.winfo_rooty()
        bottom = top + widget.winfo_height()
        total = max(self.inner.winfo_height(), 1)
        first, last = (fraction * total for fraction in self._canvas.yview())
        if top < first:
            self._canvas.yview_moveto(top / total)
        elif bottom > last:
            self._canvas.yview_moveto((bottom - (last - first)) / total)

    def follow_focus(self) -> None:
        """Every control inside, reached with the keyboard, is scrolled into view."""
        pending: list[tk.Misc] = [self.inner]
        while pending:
            widget = pending.pop()
            if widget is not self.inner:
                widget.bind("<FocusIn>", lambda event: self.see(event.widget), add="+")
            pending.extend(widget.winfo_children())

    def _destroyed(self, event: Any) -> None:
        if event.widget is self and self in ScrollArea._live:
            ScrollArea._live.remove(self)
            if not ScrollArea._live:
                for sequence in _WHEEL:
                    self.unbind_all(sequence)

    def _resized(self) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    @staticmethod
    def _dispatch(event: Any) -> None:
        for area in ScrollArea._live:
            if area.scrolls and area._over(event):
                up = event.num == 4 or getattr(event, "delta", 0) > 0
                area._canvas.yview_scroll(-1 if up else 1, "units")
                return

    def _over(self, event: Any) -> bool:
        widget = event.widget
        while isinstance(widget, tk.Misc):
            if widget is self:
                return True
            widget = widget.master
        return False
