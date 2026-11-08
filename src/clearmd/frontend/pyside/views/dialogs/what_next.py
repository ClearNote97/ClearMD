"""Results' "What Next?" (features 007, 032, 033): the three tools as small tiles with the start
screen's icons, the one just used first ("<tool> Again"), and one box for the files. One click on a
tile closes the dialog and opens step 1 of that tool; Cancel or Esc only closes it."""

from collections.abc import Callable
from functools import partial

from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QWidget

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.presenter.models import NextChoice
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.pyside.components.dialog import Dialog
from clearmd.frontend.pyside.components.primitives import button, label, restyle
from clearmd.frontend.pyside.components.tile import SMALL_ICON, Tile
from clearmd.frontend.pyside.components.tile_art import tool_art
from clearmd.i18n import Catalog

HELP_INDENT = 3 * SPACE  # the help under the box, in line with the box's words


class WhatNextDialog(Dialog):
    """The tiles (``tiles``, in the presenter's order), the box ``keep`` (ticked each time it
    opens) and Cancel; the choice goes to ``on_choose(tool, keep)``."""

    def __init__(
        self,
        parent: QWidget,
        catalog: Catalog,
        choices: tuple[NextChoice, ...],
        *,
        colour: str,
        on_choose: Callable[[Tool, bool], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(parent, title=catalog.text("gui.more.title"), on_close=on_close, width=600)
        self._on_choose = on_choose
        row = QHBoxLayout()
        row.setSpacing(GAP)
        self.tiles: list[Tile] = []
        for choice in choices:
            tile = Tile(partial(self.choose, choice.tool), small=True)
            tile.show_text(choice.title, "")
            tile.show_icon(tool_art(choice.tool, SMALL_ICON, colour))
            restyle(tile.button, "current", "true" if choice.current else "false")
            row.addWidget(tile.button, 1)
            self.tiles.append(tile)
        self.body.addLayout(row)
        self.body.addSpacing(GAP)
        self.keep = QCheckBox(catalog.text("gui.more.keep"))
        self.keep.setChecked(True)  # every time it opens
        self.body.addWidget(self.keep)
        hint = label("muted", catalog.text("gui.more.keep_help"), wrap=True)
        hint.setContentsMargins(HELP_INDENT, 0, 0, 0)
        self.body.addWidget(hint)
        self.foot.addStretch(1)
        self.cancel = button("", self.reject)
        self.cancel.setText(catalog.text("gui.more.cancel"))
        self.foot.addWidget(self.cancel)
        self.keep.setFocus()  # no tile looks pressed when it opens; Tab reaches them

    def choose(self, tool: Tool) -> None:
        keep = self.keep.isChecked()
        self.close_dialog()
        self._on_choose(tool, keep)
