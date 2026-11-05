"""The dark rail on the left (ADR-0027, ADR-0029): the logo, Clear·MD, the four steps — each one
can be opened, the one on screen highlighted, the others dimmed — Settings, Help, the version.

Below 1000 px of window width the rail is compact: the mark and the numbers only.
"""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from functools import partial
from tkinter import ttk
from typing import Literal

from PIL import ImageTk

from clearmd.frontend.design.colors import blend
from clearmd.frontend.design.metrics import COMPACT_RAIL_WIDTH, GAP, HALF, RADIUS, RAIL_WIDTH, SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.presenter.state import STEPS
from clearmd.frontend.ttk.layout import REDRAW_MS
from clearmd.frontend.ttk.visuals import marks, shapes
from clearmd.frontend.ttk.visuals.style_names import RAIL, RAIL_COMPACT
from clearmd.i18n import Catalog

_STEP_HEIGHT = 44
_TOP = 3 * SPACE  # the logo's distance from the rail's top edge
_STEPS_TOP = 12 * SPACE  # where the first step starts
_BADGE = 24  # a step's circle
_DIM = 0.55  # how strong the steps not on screen are drawn (ADR-0029)


class Rail(tk.Canvas):
    """A canvas: the rail is a picture, the steps are drawn and clickable, Settings and Help are
    buttons. ``on_step(n)`` opens step ``n``."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        fonts: dict[str, tkfont.Font],
        on_settings: Callable[[], None],
        on_help: Callable[[], None],
        on_step: Callable[[int], None],
    ) -> None:
        super().__init__(parent, width=RAIL_WIDTH + GAP, highlightthickness=0, borderwidth=0)
        self._fonts = fonts
        self._on_step = on_step
        self._palette: Palette | None = None
        self._page = 1
        self._compact = False
        self._labels = [""] * len(STEPS)
        self._local = ""
        self._version = ""
        self._texts = {"settings": "", "help": ""}
        self._pictures: list[ImageTk.PhotoImage] = []
        self._pending: str | None = None
        self.settings = ttk.Button(self, style=RAIL, command=on_settings, takefocus=True)
        self.help = ttk.Button(self, style=RAIL, command=on_help, takefocus=True)
        self.bind("<Configure>", lambda _event: self.redraw_soon())
        self.bind("<Destroy>", lambda _event: self._cancel_pending(), add="+")
        for index in range(1, len(STEPS) + 1):  # once: the items come and go, the tags stay
            tag = f"step{index}"
            self.tag_bind(tag, "<Button-1>", partial(self._clicked, index))
            self.tag_bind(tag, "<Enter>", lambda _event: self.configure(cursor="hand2"))
            self.tag_bind(tag, "<Leave>", lambda _event: self.configure(cursor=""))
        self.configure(cursor="")

    # --- What the window tells it -------------------------------------------------------------

    def show_page(self, page: int) -> None:
        if page != self._page:  # every state change calls this: draw only what changes
            self._page = page
            self._draw()

    def set_compact(self, compact: bool) -> None:
        if compact != self._compact:
            self._compact = compact
            self.configure(width=(COMPACT_RAIL_WIDTH if compact else RAIL_WIDTH) + GAP)
            self._buttons_text()
            self._draw()

    def show_version(self, version: str) -> None:
        self._version = f"v{version}" if version[:1].isdigit() else version
        self._draw()

    def apply_palette(self, palette: Palette) -> None:
        self._palette = palette
        self.configure(background=palette.ground)
        self._draw()

    def apply_language(self, catalog: Catalog) -> None:
        self._labels = [catalog.text(f"gui.steps.{name}") for name in STEPS]
        self._local = catalog.text("gui.app.local")
        self._texts = {
            "settings": catalog.text("gui.main.settings"),
            "help": catalog.text("gui.main.help_word"),
        }
        self._buttons_text()
        self._draw()

    def step_texts(self) -> list[str]:
        """The steps as drawn, the one on screen marked with ``>`` (for tests)."""
        return [
            ("> " if i + 1 == self._page else "") + label for i, label in enumerate(self._labels)
        ]

    def redraw_soon(self) -> None:
        """Draw once the size settles: a resize sends a burst of events (AC-09)."""
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

    def _buttons_text(self) -> None:
        """Settings and Help are sections of the rail like the steps (feature 011): their words
        start where the steps' words do (the style's padding, not spaces: any font); the compact
        rail shows their marks alone, centred."""
        style = RAIL_COMPACT if self._compact else RAIL
        for button in (self.settings, self.help):
            button.configure(style=style)
        if self._compact:  # icon-like texts: the full words would not fit
            self.settings.configure(text="⚙")
            self.help.configure(text="?")
        else:
            self.settings.configure(text=self._texts["settings"])
            self.help.configure(text=self._texts["help"])

    # --- Drawing -----------------------------------------------------------------------------

    def _picture(self, image: object) -> ImageTk.PhotoImage:
        picture = ImageTk.PhotoImage(image, master=self)  # type: ignore[arg-type]
        self._pictures.append(picture)
        return picture

    def _draw(self) -> None:
        self._cancel_pending()  # a draw now makes a waiting one useless
        p = self._palette
        height = self.winfo_height()
        if p is None or height < 2 * _STEPS_TOP:
            return
        self.delete("all")
        self._pictures.clear()
        left, top = GAP, GAP
        width = COMPACT_RAIL_WIDTH if self._compact else RAIL_WIDTH
        bottom = height - GAP
        ground = shapes.rounded(width, bottom - top, 2 * RADIUS, p.rail)
        self.create_image(left, top, image=self._picture(ground), anchor="nw")

        x = left + (width - 40) // 2 if self._compact else left + GAP
        logo = self._picture(marks.logo("clearmd-mark-dark-40"))
        self.create_image(x, top + _TOP, image=logo, anchor="nw")
        if not self._compact:
            mark_middle = top + _TOP + 20
            text_x = x + 40 + SPACE
            wordmark = self._fonts["wordmark"]
            for part, colour in (("Clear", p.rail_text), ("·", p.clear), ("MD", p.rail_text)):
                self.create_text(
                    text_x, mark_middle, text=part, fill=colour, font=wordmark, anchor="w"
                )
                text_x += wordmark.measure(part)

        y = top + _STEPS_TOP
        for index, label in enumerate(self._labels, start=1):
            self._draw_step(p, index, label, left, y, width)
            y += _STEP_HEIGHT + HALF

        self._draw_foot(p, left, bottom, width)

    def _draw_step(self, p: Palette, index: int, label: str, left: int, y: int, width: int) -> None:
        on_screen = index == self._page
        tag = f"step{index}"
        if on_screen:
            highlight = shapes.rounded(width - GAP, _STEP_HEIGHT, RADIUS - 2, p.accent)
            self.create_image(
                left + SPACE, y, image=self._picture(highlight), anchor="nw", tags=tag
            )
        else:  # a target for the click, the size of the step
            self.create_rectangle(
                left + SPACE, y, left + width - SPACE, y + _STEP_HEIGHT,
                fill=p.rail, outline="", tags=tag,
            )  # fmt: skip
        colour = p.on_accent if on_screen else blend(p.rail_text, p.rail, _DIM)
        middle = y + _STEP_HEIGHT // 2
        badge_x = left + width // 2 if self._compact else left + GAP + SPACE + _BADGE // 2
        circle = shapes.circle(_BADGE, outline=colour, fill=p.accent if on_screen else p.rail)
        self.create_image(badge_x, middle, image=self._picture(circle), tags=tag)
        self.create_text(
            badge_x, middle, text=str(index), fill=colour, font=self._fonts["strong"], tags=tag
        )
        if not self._compact:
            self.create_text(
                badge_x + _BADGE // 2 + SPACE + HALF, middle, text=label, fill=colour,
                font=self._fonts["strong" if on_screen else "body"], anchor="w", tags=tag,
            )  # fmt: skip

    def _clicked(self, index: int, _event: object) -> None:
        self._on_step(index)

    def _draw_foot(self, p: Palette, left: int, bottom: int, width: int) -> None:
        x = left + GAP
        foot = bottom - GAP
        body = self._fonts["body"]
        line = body.metrics("linespace")
        if self._compact:
            self.create_text(
                left + width // 2, foot, text=self._version, fill=p.rail_muted, font=body,
                anchor="s",
            )  # fmt: skip
            texts_height = line
        else:
            local = f"{self._local}\n{self._version}" if self._version else self._local
            self.create_text(
                x, foot, text=local, fill=p.rail_muted, font=body, anchor="sw",
                width=width - 2 * GAP,
            )  # fmt: skip
            lines = max(1, body.measure(self._local) // (width - 2 * GAP) + 1)
            texts_height = (lines + (1 if self._version else 0)) * line
        buttons_bottom = foot - texts_height - SPACE
        # As wide as the steps' band, their height (feature 011); centred marks when compact.
        anchor_x = left + width // 2 if self._compact else left + SPACE
        anchor: Literal["s", "sw"] = "s" if self._compact else "sw"
        band = width - GAP
        places = (
            (self.help, buttons_bottom),
            (self.settings, buttons_bottom - _STEP_HEIGHT - HALF),
        )
        for button, bottom_y in places:
            self.create_window(
                anchor_x, bottom_y, window=button, anchor=anchor, width=band, height=_STEP_HEIGHT
            )
