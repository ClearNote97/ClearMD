"""Results' "What Next?" (features 007, 032, 033): the three tools as small tiles, the one just
used first ("Convert Again"), and one box that keeps the files for whichever tile is chosen.
One click (or Enter or Space on a focused tile) closes it and opens step 1 of that tool; Cancel
or Escape only closes it."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from functools import partial
from tkinter import ttk

from PIL import Image

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.presenter.models import NextChoice
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.ttk.components.dialog import Dialog
from clearmd.frontend.ttk.components.tool_tile import ToolTile
from clearmd.frontend.ttk.visuals import tool_marks
from clearmd.frontend.ttk.visuals.style_names import MUTED, SOFT
from clearmd.i18n import Catalog

ICON = 4 * SPACE  # 32: smaller than Home's
TILE_HEIGHT = 13 * SPACE  # 104: the icon and the title, with room around
_HELP_INDENT = 3 * SPACE  # the help starts under the box's words, not under the box


class WhatNextDialog(Dialog):
    """``on_choose(tool, keep)`` runs when a tile is chosen; ``keep`` is the box."""

    def __init__(
        self,
        parent: tk.Misc,
        catalog: Catalog,
        palette: Palette,
        fonts: dict[str, tkfont.Font],
        choices: tuple[NextChoice, ...],
        on_choose: Callable[[Tool, bool], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(
            parent,
            title=catalog.text("gui.more.title"),
            palette=palette,
            fonts=fonts,
            on_close=on_close,
            width=640,
        )
        self._on_choose = on_choose
        row = ttk.Frame(self.body, style="TFrame")
        row.pack(fill="x")
        columns = range(2 * len(choices) - 1)  # tiles in the even columns, gaps in the odd ones
        row.columnconfigure(tuple(c for c in columns if c % 2 == 0), weight=1, uniform="tiles")
        row.columnconfigure(tuple(c for c in columns if c % 2), minsize=GAP)
        self.tiles: dict[Tool, ToolTile] = {}
        for index, choice in enumerate(choices):  # the presenter's order: the tool just used first
            tile = ToolTile(
                row,
                fonts=fonts,
                icon=partial(_icon, choice.tool),
                on_choose=partial(self.choose, choice.tool),
                height=TILE_HEIGHT,
                current=choice.current,
            )
            tile.configure(width=24 * SPACE)  # 192: "Convertir Otra Vez" with room
            tile.grid(row=0, column=2 * index, sticky="ew")
            tile.show_text(choice.title, "")
            tile.apply_palette(palette)
            self.tiles[choice.tool] = tile
        self.keep = tk.BooleanVar(master=self, value=True)  # ticked every time it opens
        self.keep_box = ttk.Checkbutton(
            self.body, variable=self.keep, text=catalog.text("gui.more.keep")
        )
        self.keep_box.pack(anchor="w", pady=(GAP, 0))
        ttk.Label(self.body, text=catalog.text("gui.more.keep_help"), style=MUTED).pack(
            anchor="w", padx=(_HELP_INDENT, 0)
        )
        self.cancel = ttk.Button(
            self.actions, text=catalog.text("gui.more.cancel"), style=SOFT, command=self.close
        )
        self.cancel.pack(side="right")

    def choose(self, tool: Tool) -> None:
        keep = bool(self.keep.get())
        self.close()
        self._on_choose(tool, keep)

    def answer(self, keep: bool) -> None:
        """The tool just used again, keeping the files or not (the tests' shortcut)."""
        self.keep.set(keep)
        self.choose(next(iter(self.tiles)))


def _icon(tool: Tool, colour: str) -> Image.Image:
    return tool_marks.tool_icon(tool.value, colour, ICON)
