"""The Choose step's input half: Add files / Add folder, the numbered list and the editing links.

flet 1.0 cannot receive files dropped from the system: there is no drop zone, and the empty list
says to use the two buttons (feature 018)."""

from collections.abc import Callable
from pathlib import Path

import flet as ft

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.flet.components.file_list import FileList
from clearmd.frontend.flet.components.primitives import Wording, button


class InputsCard:
    """Add files / Add folder, the numbered list, the editing links; ``controls`` in that order."""

    def __init__(
        self,
        wording: Wording,
        *,
        on_add_files: Callable[[], None],
        on_add_folder: Callable[[], None],
        on_remove: Callable[[list[Path]], None],
        on_clear: Callable[[], None],
    ) -> None:
        self._on_remove = on_remove
        self.add_files = button("", on_add_files)
        self.add_folder = button("", on_add_folder)
        wording.add(self.add_files, "gui.main.add_files")
        wording.add(self.add_folder, "gui.main.add_folder")
        entry = ft.Row([self.add_files, self.add_folder], spacing=SPACE)
        self.inputs = FileList(1, checks=True, widths=(320,))
        self.remove = button("link", self.remove_selected)
        self.clear = button("link", on_clear)
        self.deselect = button("link", self.inputs.clear_selection)
        for widget, key in (
            (self.remove, "gui.main.remove"),
            (self.clear, "gui.main.clear"),
            (self.deselect, "gui.main.deselect"),
        ):
            wording.add(widget, key)
        editing = ft.Row([self.remove, self.clear, self.deselect], spacing=SPACE)
        self.controls: list[ft.Control] = [entry, self.inputs.control, editing]

    def remove_selected(self) -> None:
        chosen = self.inputs.selected()
        if chosen:
            self._on_remove(chosen)
