"""The dark rail on the left (ADR-0027): the logo, Clear·MD, the four steps, Settings and Help."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from tkinter import ttk

from PIL import ImageTk

from clearmd.frontend.presenter.state import STEPS
from clearmd.frontend.ttk import art
from clearmd.frontend.ttk.brand import RAIL, Palette
from clearmd.frontend.ttk.layout import GAP, HALF, RADIUS, RAIL_WIDTH, SPACE
from clearmd.i18n import Catalog

_STEP_HEIGHT = 44
_TOP = 3 * SPACE  # the logo's distance from the rail's top edge
_STEPS_TOP = 12 * SPACE  # where the first step starts


class Rail(tk.Canvas):
    """A canvas: the rail is a picture, the steps are drawn, Settings and Help are buttons."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        fonts: dict[str, tkfont.Font],
        on_settings: Callable[[], None],
        on_help: Callable[[], None],
    ) -> None:
        super().__init__(parent, width=RAIL_WIDTH + GAP, highlightthickness=0, borderwidth=0)
        self._fonts = fonts
        self._palette: Palette | None = None
        self._step = 1
        self._labels = [""] * len(STEPS)
        self._local = ""
        self._pictures: list[ImageTk.PhotoImage] = []
        self.settings = ttk.Button(self, style=RAIL, command=on_settings, takefocus=True)
        self.help = ttk.Button(self, style=RAIL, command=on_help, takefocus=True)
        self.bind("<Configure>", lambda _event: self._draw())

    # --- What the window tells it -------------------------------------------------------------

    def show_step(self, step: int) -> None:
        self._step = step
        self._draw()

    def apply_palette(self, palette: Palette) -> None:
        self._palette = palette
        self.configure(background=palette.ground)
        self._draw()

    def apply_language(self, catalog: Catalog) -> None:
        self._labels = [catalog.text(f"gui.steps.{name}") for name in STEPS]
        self._local = catalog.text("gui.app.local")
        self.settings.configure(text=catalog.text("gui.main.settings"))
        self.help.configure(text=catalog.text("gui.main.help"))
        self._draw()

    def step_texts(self) -> list[str]:
        """The steps as drawn, the current one first-marked with ``>`` (for tests)."""
        return [
            ("> " if i + 1 == self._step else "") + label for i, label in enumerate(self._labels)
        ]

    # --- Drawing -----------------------------------------------------------------------------

    def _picture(self, image: object) -> ImageTk.PhotoImage:
        picture = ImageTk.PhotoImage(image, master=self)  # type: ignore[arg-type]
        self._pictures.append(picture)
        return picture

    def _draw(self) -> None:
        p = self._palette
        height = self.winfo_height()
        if p is None or height < 2 * _STEPS_TOP:
            return
        self.delete("all")
        self._pictures.clear()
        left, top = GAP, GAP
        width, bottom = RAIL_WIDTH, height - GAP
        ground = art.rounded(width, bottom - top, 2 * RADIUS, p.rail)
        self.create_image(left, top, image=self._picture(ground), anchor="nw")

        x = left + GAP
        logo = self._picture(art.logo("clearmd-mark-dark-40"))
        self.create_image(x, top + _TOP, image=logo, anchor="nw")
        mark_middle = top + _TOP + 20
        text_x = x + 40 + SPACE
        wordmark = self._fonts["wordmark"]
        for part, colour in (("Clear", p.rail_text), ("·", p.clear), ("MD", p.rail_text)):
            self.create_text(text_x, mark_middle, text=part, fill=colour, font=wordmark, anchor="w")
            text_x += wordmark.measure(part)

        y = top + _STEPS_TOP
        for index, label in enumerate(self._labels, start=1):
            current = index == self._step
            if current:
                highlight = art.rounded(width - GAP, _STEP_HEIGHT, RADIUS - 2, p.accent)
                self.create_image(left + SPACE, y, image=self._picture(highlight), anchor="nw")
            text = p.on_accent if current else p.rail_text
            badge_x, middle = left + GAP + SPACE + 12, y + _STEP_HEIGHT / 2
            self.create_oval(
                badge_x - 12, middle - 12, badge_x + 12, middle + 12,
                outline=text if not current else p.on_accent,
                fill=p.accent if current else p.rail,
                width=1,
            )  # fmt: skip
            self.create_text(
                badge_x, middle, text=str(index), fill=text, font=self._fonts["strong"]
            )
            self.create_text(
                badge_x + 12 + SPACE + HALF,
                middle,
                text=label,
                fill=text,
                font=self._fonts["strong" if current else "body"],
                anchor="w",
            )
            y += _STEP_HEIGHT + HALF

        foot = bottom - GAP
        self.create_text(
            x, foot, text=self._local, fill=p.rail_muted, font=self._fonts["body"],
            anchor="sw", width=width - 2 * GAP,
        )  # fmt: skip
        lines = max(1, self._fonts["body"].measure(self._local) // (width - 2 * GAP) + 1)
        buttons_bottom = foot - lines * self._fonts["body"].metrics("linespace") - SPACE
        self.create_window(x - SPACE, buttons_bottom, window=self.help, anchor="sw")
        self.create_window(x - SPACE, buttons_bottom - 44 - HALF, window=self.settings, anchor="sw")
