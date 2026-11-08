"""Home, the start screen (features 023, 026; ADR-0043): what the user wants to do. Three large
tiles, Convert to Markdown, Split a Document and Merge Documents, and under them the line that
says the tools change files, never what is inside them. The header (title and subtitle) is the
surface's, as on every page."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from functools import partial
from tkinter import ttk

from clearmd.frontend.design.metrics import GAP
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.ttk.components.tool_tile import ToolTile
from clearmd.frontend.ttk.visuals import tool_marks
from clearmd.frontend.ttk.visuals.style_names import CARD, MUTED, PAGE
from clearmd.i18n import Catalog

_TILES = (  # the tool, its icon, the catalog keys of its title and its body
    (Tool.CONVERT, tool_marks.document, "gui.home.convert", "gui.home.convert_body"),
    (Tool.SPLIT, tool_marks.scissors, "gui.home.split", "gui.home.split_body"),
    (Tool.MERGE, tool_marks.merge, "gui.home.merge", "gui.home.merge_body"),  # feature 026
)


class HomeView(ttk.Frame):
    """The tiles side by side in a card, equally wide, the note centred under them."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        fonts: dict[str, tkfont.Font],
        on_tool: Callable[[Tool], None],
    ) -> None:
        super().__init__(parent, style=PAGE)
        card = ttk.Frame(self, style=CARD, padding=2 * GAP)
        card.pack(fill="both", expand=True)
        # Tiles in the even columns, all as wide; the gaps between them in the odd ones.
        columns = range(2 * len(_TILES) - 1)
        card.columnconfigure(tuple(c for c in columns if c % 2 == 0), weight=1, uniform="tiles")
        card.columnconfigure(tuple(c for c in columns if c % 2), minsize=GAP)
        card.rowconfigure((0, 3), weight=1)  # the tiles and the note, in the middle
        self.tiles: dict[Tool, ToolTile] = {}
        self._keys: dict[Tool, tuple[str, str]] = {}
        for index, (tool, icon, title, body) in enumerate(_TILES):
            tile = ToolTile(card, fonts=fonts, icon=icon, on_choose=partial(on_tool, tool))
            tile.grid(row=1, column=2 * index, sticky="ew")
            self.tiles[tool] = tile
            self._keys[tool] = (title, body)
        self.note = ttk.Label(card, style=MUTED, anchor="center", justify="center")
        self.note.grid(row=2, column=0, columnspan=len(columns), sticky="ew", pady=(GAP, 0))
        card.bind(
            "<Configure>", lambda event: self.note.configure(wraplength=event.width - 4 * GAP)
        )

    def apply_language(self, catalog: Catalog) -> None:
        for tool, tile in self.tiles.items():
            title, body = self._keys[tool]
            tile.show_text(catalog.text(title), catalog.text(body))
        self.note.configure(text=catalog.text("gui.home.files_note"))

    def apply_palette(self, palette: Palette) -> None:
        for tile in self.tiles.values():
            tile.apply_palette(palette)
