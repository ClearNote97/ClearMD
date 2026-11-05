"""The dark rail on the left (ADR-0027, ADR-0029): the logo, Clear·MD, the four steps — each one
can be opened, the one on screen highlighted, the others dimmed — Settings, Help, the version.

Below 1000 px of window width the rail is compact: the mark and the numbers only.
"""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from functools import partial
from tkinter import ttk

from PIL import ImageTk

from clearmd.frontend.design.metrics import COMPACT_RAIL_WIDTH, GAP, RAIL_WIDTH
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.presenter.state import STEPS
from clearmd.frontend.ttk.components.rail_art import STEPS_TOP, Scene, draw_rail
from clearmd.frontend.ttk.layout.units import REDRAW_MS
from clearmd.frontend.ttk.visuals.style_names import RAIL, RAIL_COMPACT
from clearmd.i18n import Catalog


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
        if p is None or height < 2 * STEPS_TOP:
            return
        self.delete("all")
        self._pictures.clear()
        scene = Scene(
            self._fonts, self._page, self._compact, self._labels, self._local, self._version
        )
        draw_rail(self, self._picture, p, scene, height, (self.settings, self.help))

    def _clicked(self, index: int, _event: object) -> None:
        self._on_step(index)
