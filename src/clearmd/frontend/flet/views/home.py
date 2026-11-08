"""Home, the start screen (features 023, 026; ADR-0043): what the user wants to do, as three large
tiles, Convert to Markdown, Split a Document and Merge Documents, and the line that says the tools
change files, never what is inside them. The page's title and subtitle are the surface's header,
as on every step."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.flet.components.primitives import Wording, label
from clearmd.frontend.flet.components.start_panel import Tile
from clearmd.frontend.flet.components.tool_icon import tool_icon
from clearmd.frontend.presenter.state import Tool
from clearmd.i18n import Catalog

HOME_TILE_HEIGHT = 24 * SPACE  # 192: larger than step 1's tiles, the page's one choice
HOME_ICON_SIZE = 7 * SPACE  # 56
HOME_TOP = 4 * SPACE  # the content from the top, as Qt's: icons and titles in line (024)


class HomeView:
    """The three tools' tiles side by side, of equal width, the note centered under them."""

    def __init__(self, *, on_tool: Callable[[Tool], None]) -> None:
        self._wording = Wording()
        self.convert = Tile(
            self._wording,
            tool_icon(Tool.CONVERT, HOME_ICON_SIZE),
            "gui.home.convert",
            "gui.home.convert_body",
            lambda: on_tool(Tool.CONVERT),
            height=HOME_TILE_HEIGHT,
            icon_size=HOME_ICON_SIZE,
            top=HOME_TOP,
        )
        self.split = Tile(
            self._wording,
            tool_icon(Tool.SPLIT, HOME_ICON_SIZE),
            "gui.home.split",
            "gui.home.split_body",
            lambda: on_tool(Tool.SPLIT),
            height=HOME_TILE_HEIGHT,
            icon_size=HOME_ICON_SIZE,
            top=HOME_TOP,
        )
        self.merge = Tile(
            self._wording,
            tool_icon(Tool.MERGE, HOME_ICON_SIZE),
            "gui.home.merge",
            "gui.home.merge_body",
            lambda: on_tool(Tool.MERGE),
            height=HOME_TILE_HEIGHT,
            icon_size=HOME_ICON_SIZE,
            top=HOME_TOP,
        )
        self.tiles = (self.convert, self.split, self.merge)
        self.note = label("hint")
        self.note.text_align = ft.TextAlign.CENTER
        self._wording.add(self.note, "gui.home.files_note")
        row = ft.Row([tile.control for tile in self.tiles], spacing=GAP)  # equal widths
        # Centred in the page, the note just under the tiles, as Qt's and ttk's (feature 032).
        self.control = ft.Column(
            [row, self.note],
            spacing=GAP,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def apply_language(self, catalog: Catalog) -> None:
        self._wording.apply(catalog)
