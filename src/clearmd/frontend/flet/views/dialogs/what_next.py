"""Results' "What Next?" (features 007, 032, 033): the three tools as small tiles, the one just
used first ("Convert Again"), and one box for the files, ticked every time it opens. One click on
a tile closes the dialog and opens step 1 of that tool; Cancel (or Esc) only closes it."""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.design.metrics import GAP, HALF, SPACE
from clearmd.frontend.flet.components.dialog import Dialog
from clearmd.frontend.flet.components.primitives import button, gap, label, stretch
from clearmd.frontend.flet.components.tool_icon import tool_icon
from clearmd.frontend.flet.layout.units import CHECK_WIDTH, QUESTION_WIDTH
from clearmd.frontend.flet.visuals.look import text_style, tile_style
from clearmd.frontend.presenter.models import NextChoice
from clearmd.frontend.presenter.state import Tool
from clearmd.i18n import Catalog

ICON = 4 * SPACE  # 32: smaller than Home's
TILE_HEIGHT = 13 * SPACE  # 104: the icon and a title of up to two lines


class WhatNextDialog(Dialog):
    """``tiles`` in the presenter's order, ``keep`` (the box), ``cancel``; a tile's click goes to
    ``on_choose(tool, keep)``."""

    def __init__(
        self,
        catalog: Catalog,
        choices: tuple[NextChoice, ...],
        *,
        on_choose: Callable[[Tool, bool], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(
            title=catalog.text("gui.more.title"), on_close=on_close, width=QUESTION_WIDTH
        )
        self._on_choose = on_choose
        self.tiles = {choice.tool: self._tile(choice) for choice in choices}
        self.keep = ft.Checkbox(
            value=True, label=catalog.text("gui.more.keep"), label_style=text_style("onPage")
        )
        self.keep_help = label("muted", catalog.text("gui.more.keep_help"))
        help_line = ft.Container(content=self.keep_help, padding=ft.Padding.only(left=CHECK_WIDTH))
        self.body.controls.extend(
            [
                ft.Row(list(self.tiles.values()), spacing=GAP),
                gap(GAP),
                self.keep,
                help_line,
            ]
        )
        self.cancel = button("", self.close_dialog, catalog.text("gui.more.cancel"))
        self.foot.controls.extend([stretch(), self.cancel])
        if choices:  # Enter: the tool just used again, as its tile
            first = choices[0].tool
            self.default(lambda: self.choose(first))

    def _tile(self, choice: NextChoice) -> ft.Button:
        title = label("strong", choice.title)
        title.text_align = ft.TextAlign.CENTER
        column = ft.Column(
            [tool_icon(choice.tool, ICON), title],
            spacing=HALF,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        tile = ft.Button(
            content=column,
            style=tile_style(GAP, current=choice.current),  # the one just used: accent border
            height=TILE_HEIGHT,
            expand=True,
            on_click=lambda: self.choose(choice.tool),
        )
        tile.tooltip = choice.title
        return tile

    def choose(self, tool: Tool) -> None:
        keep = bool(self.keep.value)
        self.close_dialog()
        self._on_choose(tool, keep)
