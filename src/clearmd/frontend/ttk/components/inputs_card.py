"""The Choose step's input half: Add files / Add folder, the drop zone, the numbered list and the
editing links. It builds its widgets on the step's own frame, so the layout stays the step's."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk
from typing import Any

from clearmd.frontend.design.metrics import GAP, HALF, SPACE
from clearmd.frontend.ttk.components.drop_zone import DropZone
from clearmd.frontend.ttk.components.file_list import Column, FileList
from clearmd.frontend.ttk.visuals.style_names import LINK, PAGE, SOFT

TALL_DROP = 11 * SPACE  # the drop zone beside the two buttons, one over the other
SHORT_DROP = 6 * SPACE  # beside them side by side, in a short window (review of 011)


class InputsCard:
    """Add files / Add folder and the drop zone, the numbered list, the editing links."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        fonts: dict[str, tkfont.Font],
        on_add_files: Callable[[], None],
        on_add_folder: Callable[[], None],
        on_remove: Callable[[list[Path]], None],
        on_clear: Callable[[], None],
        label: Callable[[Any, str], None],
    ) -> None:
        self._on_remove = on_remove
        entry = ttk.Frame(parent, style=PAGE)
        entry.pack(fill="x")
        buttons = ttk.Frame(entry, style=PAGE)
        buttons.pack(side="left", fill="y")
        self.add_files = ttk.Button(buttons, style=SOFT, command=on_add_files)
        self.add_folder = ttk.Button(buttons, style=SOFT, command=on_add_folder)
        self._short = False
        self._stack_buttons()
        label(self.add_files, "gui.main.add_files")
        label(self.add_folder, "gui.main.add_folder")
        self.drop_zone = DropZone(entry, fonts=fonts, on_click=on_add_files)
        self.drop_zone.pack(side="left", fill="both", expand=True, padx=(GAP, 0))

        self.inputs = FileList(
            parent,
            name_heading="gui.main.column_name",
            columns=(Column("location", 320, stretch=True),),
            height=4,
        )
        self.inputs.pack(fill="both", expand=True, pady=(GAP, 0))
        self.inputs.tree.bind("<Delete>", lambda _event: self._remove_selected())

        self.editing = ttk.Frame(parent, style=PAGE)
        # The output card and the editing links stay at the bottom; the list takes what is left,
        # so nothing is cut at the smallest window (code review of 007).
        self.editing.pack(side="bottom", fill="x", pady=(HALF, 0), before=self.inputs)
        self.remove = ttk.Button(self.editing, style=LINK, command=self._remove_selected)
        self.remove.pack(side="left")
        self.clear = ttk.Button(self.editing, style=LINK, command=on_clear)
        self.clear.pack(side="left", padx=(SPACE, 0))
        self.deselect = ttk.Button(self.editing, style=LINK, command=self.inputs.clear_selection)
        self.deselect.pack(side="left", padx=(SPACE, 0))
        label(self.deselect, "gui.main.deselect")
        label(self.remove, "gui.main.remove")
        label(self.clear, "gui.main.clear")

    def set_short(self, short: bool) -> None:
        """A short window: the add buttons side by side and a lower drop zone, so the list keeps
        its rows (review of 011: at 800 x 560 it had none)."""
        if short != self._short:
            self._short = short
            self._stack_buttons()

    def _stack_buttons(self) -> None:
        self.add_files.pack_forget()
        self.add_folder.pack_forget()
        if self._short:
            self.add_files.pack(side="left", fill="y")
            self.add_folder.pack(side="left", fill="y", padx=(SPACE, 0))
            if hasattr(self, "drop_zone"):
                self.drop_zone.configure(height=SHORT_DROP)
        else:
            self.add_files.pack(fill="x")
            self.add_folder.pack(fill="x", pady=(SPACE, 0))
            if hasattr(self, "drop_zone"):
                self.drop_zone.configure(height=TALL_DROP)

    def _remove_selected(self) -> None:
        chosen = self.inputs.selected()
        if chosen:
            self._on_remove(chosen)
