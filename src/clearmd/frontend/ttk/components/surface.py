"""The working area (ADR-0027): the ground with its soft shape, a header, and the current page."""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from PIL import ImageTk

from clearmd.frontend.ttk import art
from clearmd.frontend.ttk.brand import PAGE, Palette
from clearmd.frontend.ttk.layout import (
    GAP,
    GUTTER,
    HALF,
    INSET,
    MARGIN,
    RADIUS,
    REDRAW_MS,
)


class Surface(tk.Canvas):
    """Header texts are canvas text, so the shape shows behind them; the page is a frame below."""

    def __init__(self, parent: tk.Misc, *, fonts: dict[str, tkfont.Font]) -> None:
        super().__init__(parent, highlightthickness=0, borderwidth=0)
        self._fonts = fonts
        self._palette: Palette | None = None
        self._texts = {"eyebrow": "", "title": "", "subtitle": ""}
        self._ground: ImageTk.PhotoImage | None = None
        self._ground_key: tuple[int, int, str, int] | None = (
            None  # drawn again only when it changes
        )
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
        x, y = GUTTER, GUTTER  # the header starts where the card does
        self.create_text(
            x, y, text=self._texts["eyebrow"].upper(), fill=p.accent_text,
            font=self._fonts["eyebrow"], anchor="nw",
        )  # fmt: skip
        y += self._fonts["body"].metrics("linespace") + HALF
        self.create_text(
            x, y, text=self._texts["title"], fill=p.text, font=self._fonts["title"], anchor="nw"
        )
        y += self._fonts["title"].metrics("linespace") + HALF
        subtitle = self.create_text(
            x, y, text=self._texts["subtitle"], fill=p.muted, font=self._fonts["body"],
            anchor="nw", width=width - 2 * MARGIN,
        )  # fmt: skip
        # The header ends where its subtitle does, wrapped or not (review of 011).
        box = self.bbox(subtitle)
        top = max(box[3] if box else y, self._header_height()) + GAP
        key = (width, height, p.mode, top)
        new_theme = self._ground_key is None or self._ground_key[2] != p.mode
        if self._ground is None or (key != self._ground_key and (paint or new_theme)):
            picture = art.surface(width, height, p.ground, p.shape, band=top)
            self._ground = ImageTk.PhotoImage(picture, master=self)
            self._ground_key = key
        ground = self.create_image(0, 0, image=self._ground, anchor="nw")
        self.tag_lower(ground)
        # The page's card outline: canvas lines, so it follows a resize at once (review of 011).
        # The same gutter on every side: from the rail, to the window's edges, and inside it.
        if height - GUTTER - top > 2 * RADIUS:
            self._outline(GUTTER, top, width - GUTTER, height - GUTTER, p.border)
        self.create_window(
            GUTTER + INSET, top + INSET, window=self.page, anchor="nw",
            width=width - 2 * GUTTER - 2 * INSET, height=height - top - GUTTER - 2 * INSET,
        )  # fmt: skip

    def _outline(self, left: int, top: int, right: int, bottom: int, colour: str) -> None:
        r = RADIUS
        points = [
            left + r, top, right - r, top, right, top, right, top + r,
            right, bottom - r, right, bottom, right - r, bottom, left + r, bottom,
            left, bottom, left, bottom - r, left, top + r, left, top,
        ]  # fmt: skip
        self.create_polygon(points, smooth=True, fill="", outline=colour, width=1)
