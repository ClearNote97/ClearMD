"""Home, the start screen (feature 023, ADR-0043): what the user wants to do, as two large tiles,
Convert to Markdown and Split a PDF, and the line that says the tools change files, never what is
inside them. The page's title and subtitle are the surface's header, as on every step."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.flet.components.primitives import Wording, label
from clearmd.frontend.flet.components.start_panel import Tile
from clearmd.frontend.presenter.state import Tool
from clearmd.i18n import Catalog

HOME_TILE_HEIGHT = 25 * SPACE  # 200: larger than step 1's tiles, the page's one choice
HOME_ICON_SIZE = 7 * SPACE  # 56


class HomeView:
    """The two tools' tiles side by side, the note centered under them."""

    def __init__(self, *, on_tool: Callable[[Tool], None]) -> None:
        self._wording = Wording()
        self.convert = Tile(
            self._wording,
            ft.Icons.DESCRIPTION_OUTLINED,
            "gui.home.convert",
            "gui.home.convert_body",
            lambda: on_tool(Tool.CONVERT),
            height=HOME_TILE_HEIGHT,
            icon_size=HOME_ICON_SIZE,
        )
        self.split = Tile(
            self._wording,
            ft.Icons.CONTENT_CUT,
            "gui.home.split",
            "gui.home.split_body",
            lambda: on_tool(Tool.SPLIT),
            height=HOME_TILE_HEIGHT,
            icon_size=HOME_ICON_SIZE,
        )
        self.tiles = (self.convert, self.split)
        self.note = label("hint")
        self.note.text_align = ft.TextAlign.CENTER
        self._wording.add(self.note, "gui.home.files_note")
        row = ft.Row([self.convert.control, self.split.control], spacing=GAP)
        self.control = ft.Column(
            [row, self.note],
            spacing=GAP,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def apply_language(self, catalog: Catalog) -> None:
        self._wording.apply(catalog)
