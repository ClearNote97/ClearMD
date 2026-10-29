"""The working area (ADR-0027): the ground with its soft shape, a header, and the current page."""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from PIL import ImageTk

from clearmd.frontend.ttk import art
from clearmd.frontend.ttk.brand import PAGE, Palette
from clearmd.frontend.ttk.layout import GAP, HALF, MARGIN, REDRAW_MS, SPACE


class Surface(tk.Canvas):
    """Header texts are canvas text, so the shape shows behind them; the page is a frame below."""

    def __init__(self, parent: tk.Misc, *, fonts: dict[str, tkfont.Font]) -> None:
        super().__init__(parent, highlightthickness=0, borderwidth=0)
        self._fonts = fonts
        self._palette: Palette | None = None
        self._texts = {"eyebrow": "", "title": "", "subtitle": ""}
        self._ground: ImageTk.PhotoImage | None = None
        self._ground_key: tuple[int, int, str] | None = None  # drawn again only when it changes
        self.page = ttk.Frame(self, style=PAGE)
        self._pending: str | None = None
        self.bind("<Destroy>", lambda _event: self._cancel_pending(), add="+")
        self.bind("<Configure>", lambda _event: self._resized())

    def apply_palette(self, palette: Palette) -> None:
        self._palette = palette
        self.configure(background=palette.ground)
        self._draw()

    def show_header(self, *, eyebrow: str, title: str, subtitle: str) -> None:
        self._texts = {"eyebrow": eyebrow, "title": title, "subtitle": subtitle}
        self._draw()

    def header(self) -> dict[str, str]:
        return dict(self._texts)

    def _header_height(self) -> int:
        body = self._fonts["body"].metrics("linespace")
        title = self._fonts["title"].metrics("linespace")
        return GAP + body + HALF + title + HALF + body

    def _redraw_now(self) -> None:
        self._pending = None
        self._draw()

    def _cancel_pending(self) -> None:
        """A redraw still waiting when the window closes is dropped (code review of 007)."""
        if self._pending is not None:
            self.after_cancel(self._pending)
            self._pending = None

    def _resized(self) -> None:
        """Lay out at once; draw the ground again only once the size settles (AC-09)."""
        self._draw(paint=False)
        if self._pending is not None:
            self.after_cancel(self._pending)
        self._pending = self.after(REDRAW_MS, self._redraw_now)

    def _draw(self, *, paint: bool = True) -> None:
        self._cancel_pending()  # a draw now makes a waiting one useless
        p = self._palette
        width, height = self.winfo_width(), self.winfo_height()
        if p is None or width < 2 * MARGIN or height < 2 * MARGIN:
            return
        self.delete("all")
        key = (width, height, p.mode)
        new_theme = self._ground_key is None or self._ground_key[2] != p.mode
        if self._ground is None or (key != self._ground_key and (paint or new_theme)):
            picture = art.surface(width, height, p.ground, p.shape)
            self._ground = ImageTk.PhotoImage(picture, master=self)
            self._ground_key = (width, height, p.mode)
        self.create_image(0, 0, image=self._ground, anchor="nw")
        x, y = SPACE, GAP
        self.create_text(
            x, y, text=self._texts["eyebrow"].upper(), fill=p.accent_text,
            font=self._fonts["eyebrow"], anchor="nw",
        )  # fmt: skip
        y += self._fonts["body"].metrics("linespace") + HALF
        self.create_text(
            x, y, text=self._texts["title"], fill=p.text, font=self._fonts["title"], anchor="nw"
        )
        y += self._fonts["title"].metrics("linespace") + HALF
        self.create_text(
            x, y, text=self._texts["subtitle"], fill=p.muted, font=self._fonts["body"],
            anchor="nw", width=width - 2 * MARGIN,
        )  # fmt: skip
        top = self._header_height() + GAP
        self.create_window(
            SPACE, top, window=self.page, anchor="nw",
            width=width - SPACE - GAP, height=height - top - GAP,
        )  # fmt: skip
