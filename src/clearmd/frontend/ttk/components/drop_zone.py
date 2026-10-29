"""Where files and folders can be dropped (ADR-0027): a dashed, rounded zone; a click adds files."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable

from PIL import ImageTk

from clearmd.frontend.ttk import art
from clearmd.frontend.ttk.brand import Palette
from clearmd.frontend.ttk.layout import RADIUS, REDRAW_MS, SPACE


class DropZone(tk.Canvas):
    def __init__(
        self, parent: tk.Misc, *, fonts: dict[str, tkfont.Font], on_click: Callable[[], None]
    ) -> None:
        super().__init__(parent, height=11 * SPACE, highlightthickness=0, borderwidth=0)
        self._fonts = fonts
        self._palette: Palette | None = None
        self._text = ""
        self._picture: ImageTk.PhotoImage | None = None
        self.configure(cursor="hand2")
        self._pending: str | None = None
        self.bind("<Configure>", lambda _event: self._resized())
        self.bind("<Button-1>", lambda _event: on_click())

    def apply_palette(self, palette: Palette) -> None:
        self._palette = palette
        self.configure(background=palette.ground)
        self._draw()

    def show_text(self, text: str) -> None:
        self._text = text
        self._draw()

    def text(self) -> str:
        return self._text

    def _resized(self) -> None:
        """A dashed border is a picture: drawn again only once the size settles (AC-09)."""
        if self._pending is not None:
            self.after_cancel(self._pending)
        self._pending = self.after(REDRAW_MS, self._draw)

    def _draw(self) -> None:
        self._pending = None
        p = self._palette
        width, height = self.winfo_width(), self.winfo_height()
        if p is None or width < 4 * RADIUS:
            return
        self.delete("all")
        shape = art.rounded(width, height, RADIUS, p.card, border=p.muted, dashed=True)
        self._picture = ImageTk.PhotoImage(shape, master=self)
        self.create_image(0, 0, image=self._picture, anchor="nw")
        middle = height / 2
        body = self._fonts["body"]
        arrow = self._fonts["title"]
        text_width = body.measure(self._text)
        left = (width - text_width - arrow.measure("↓") - SPACE) / 2
        self.create_text(left, middle, text="↓", fill=p.accent_text, font=arrow, anchor="w")
        self.create_text(
            left + arrow.measure("↓") + SPACE, middle, text=self._text, fill=p.muted, font=body,
            anchor="w",
        )  # fmt: skip
