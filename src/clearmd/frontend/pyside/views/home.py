"""The start screen (feature 023, ADR-0043): what the user wants to do. Two large tiles side by
side, Convert to Markdown and Split a PDF, and under them the line that says the tools change
files, never their content. The header is the page's own (the surface draws it)."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from clearmd.frontend.design.metrics import GAP
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.pyside.components.primitives import card, label
from clearmd.frontend.pyside.components.tile import ICON_SIZE, Tile
from clearmd.frontend.pyside.components.tile_art import document_art, scissors_art
from clearmd.i18n import Catalog


class HomeView(QWidget):
    """The two tiles and the note; a tile opens step 1 of its tool."""

    def __init__(self, *, on_convert: Callable[[], None], on_split: Callable[[], None]) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        frame, layout = card(padding=2 * GAP)  # as flet's start panel: the tiles in a card
        layout.setSpacing(GAP)
        outer.addWidget(frame, 1)
        layout.addStretch(1)
        tiles = QHBoxLayout()
        tiles.setSpacing(GAP)
        self.convert = Tile(on_convert)
        self.split = Tile(on_split)
        for tile in (self.convert, self.split):
            tiles.addWidget(tile.button, 1)
        layout.addLayout(tiles)
        self.note = label("hint", wrap=True)
        self.note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.note)
        layout.addStretch(1)
        self.tiles = (self.convert.button, self.split.button)

    def apply_language(self, catalog: Catalog) -> None:
        text = catalog.text
        self.convert.show_text(text("gui.home.convert"), text("gui.home.convert_body"))
        self.split.show_text(text("gui.home.split"), text("gui.home.split_body"))
        self.note.setText(text("gui.home.files_note"))

    def apply_palette(self, palette: Palette) -> None:
        self.convert.show_icon(document_art(ICON_SIZE, palette.accent_text))
        self.split.show_icon(scissors_art(ICON_SIZE, palette.accent_text))
