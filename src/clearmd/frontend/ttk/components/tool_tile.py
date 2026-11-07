"""A large tile of the start screen (feature 023): an icon, a title and what the tool does.

As flet's tiles of 021: the page's ground on the card, a 1 px border; under the pointer or with
the keyboard's focus, the accent's border and the selection's ground. Enter or Space opens it.
"""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from functools import partial

from PIL import Image, ImageDraw, ImageTk

from clearmd.frontend.design.colors import blend
from clearmd.frontend.design.metrics import GAP, HALF, RADIUS, SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.ttk.layout.units import REDRAW_MS
from clearmd.frontend.ttk.visuals.shapes import SUPERSAMPLE, rgba

TILE_HEIGHT = 22 * SPACE  # 176: the icon, the title and two lines of text, with room around
SELECTED = 0.18  # the selection's ground: this much of the accent on the card (as flet and Qt)

Icon = Callable[[str], Image.Image]  # the icon, drawn in a colour


def ground(width: int, height: int, fill: str, line: str, thickness: int, card: str) -> Image.Image:
    """The tile's rounded ground and border; its corners show the ``card`` it sits on."""
    s = SUPERSAMPLE
    big = Image.new("RGBA", (width * s, height * s), rgba(card))
    draw = ImageDraw.Draw(big)
    draw.rounded_rectangle(
        (0, 0, width * s - 1, height * s - 1), RADIUS * s, fill=rgba(fill),
        outline=rgba(line), width=thickness * s,
    )  # fmt: skip
    return big.resize((width, height), Image.Resampling.LANCZOS)


class ToolTile(tk.Canvas):
    """A button drawn on a canvas; ``on_choose`` runs on a click, Enter or Space."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        fonts: dict[str, tkfont.Font],
        icon: Icon,
        on_choose: Callable[[], None],
    ) -> None:
        super().__init__(
            parent, height=TILE_HEIGHT, highlightthickness=0, borderwidth=0, takefocus=True
        )
        self._fonts = fonts
        self._icon = icon
        self._on_choose = on_choose
        self._palette: Palette | None = None
        self._texts = ("", "")
        self._hovered = False
        self._focused = False
        self._pictures: list[ImageTk.PhotoImage] = []
        self._pending: str | None = None
        self.configure(cursor="hand2")
        self.bind("<Configure>", lambda _event: self._resized())
        self.bind("<Destroy>", lambda _event: self._cancel_pending(), add="+")
        self.bind("<Button-1>", lambda _event: self.choose())
        for key in ("<Return>", "<KP_Enter>", "<space>"):
            self.bind(key, self._key)
        # Lit under the pointer from its first move (decoration only: AC-19 of 005 keeps every
        # control reachable without hover, and the focus lights it the same way).
        for event, field, value in (
            ("<Motion>", "_hovered", True),
            ("<Leave>", "_hovered", False),
            ("<FocusIn>", "_focused", True),
            ("<FocusOut>", "_focused", False),
        ):
            self.bind(event, partial(self._mark, field, value))

    # --- What the view tells it ----------------------------------------------------------------

    def show_text(self, title: str, body: str) -> None:
        self._texts = (title, body)
        self._draw()

    def apply_palette(self, palette: Palette) -> None:
        self._palette = palette
        self.configure(background=palette.card)
        self._draw()

    def texts(self) -> tuple[str, str]:
        return self._texts

    @property
    def lit(self) -> bool:
        """Drawn as chosen: under the pointer, or with the focus."""
        return self._hovered or self._focused

    def choose(self) -> None:
        self._on_choose()

    # --- Events and drawing --------------------------------------------------------------------

    def _key(self, _event: object) -> str:
        self.choose()
        return "break"  # the window's own Enter (the primary action) must not run too

    def _mark(self, field: str, value: bool, _event: object) -> None:
        if getattr(self, field) != value:
            setattr(self, field, value)
            self._draw()

    def _resized(self) -> None:
        if self._pending is not None:
            self.after_cancel(self._pending)
        self._pending = self.after(REDRAW_MS, self._redraw_now)

    def _redraw_now(self) -> None:
        self._pending = None
        self._draw()

    def _cancel_pending(self) -> None:
        if self._pending is not None:
            self.after_cancel(self._pending)
            self._pending = None

    def _draw(self) -> None:
        self._cancel_pending()
        p = self._palette
        width, height = self.winfo_width(), self.winfo_height()
        if p is None or width < 4 * RADIUS or height < 4 * RADIUS:
            return
        self.delete("all")
        self._pictures.clear()
        if self.lit:
            fill, line, thickness = blend(p.accent, p.card, SELECTED), p.accent, 2
        else:
            fill, line, thickness = p.ground, p.border, 1
        self._image(ground(width, height, fill, line, thickness, p.card), 0, 0, "nw")
        title, body = self._texts
        strong, text = self._fonts["strong"], self._fonts["body"]
        icon = self._icon(p.accent_text)
        # Room for two lines of body in every tile: the icons and titles of both tiles line up.
        lines = max(2, text.measure(body) // max(width - 2 * GAP, 1) + 1)
        block = icon.height + HALF + strong.metrics("linespace") + HALF
        block += lines * text.metrics("linespace")
        y = max(GAP, (height - block) // 2)
        self._image(icon, width // 2, y, "n")
        y += icon.height + HALF
        self.create_text(width // 2, y, text=title, fill=p.text, font=strong, anchor="n")
        y += strong.metrics("linespace") + HALF
        self.create_text(
            width // 2, y, text=body, fill=p.muted, font=text, anchor="n", justify="center",
            width=width - 2 * GAP,
        )  # fmt: skip

    def _image(self, picture: Image.Image, x: int, y: int, anchor: str) -> None:
        image = ImageTk.PhotoImage(picture, master=self)
        self._pictures.append(image)  # Tk forgets an image Python does not hold
        self.create_image(x, y, image=image, anchor=anchor)
