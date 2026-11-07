"""The Choose step's input half: Add files / Add folder, the numbered list and the editing links.

flet 1.0 cannot receive files dropped from the system. Before anything is chosen, the list's room
holds two large tiles, Add files and Add folder (feature 021); the small buttons, the list and its
links come once something is listed."""

from collections.abc import Callable
from pathlib import Path

import flet as ft

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.flet.components.file_list import FileList
from clearmd.frontend.flet.components.primitives import Wording, button
from clearmd.frontend.flet.components.start_panel import StartPanel


class InputsCard:
    """Add files / Add folder, the numbered list, the editing links, and the start tiles in their
    place while nothing is listed; ``controls`` in that order."""

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
        self.entry = ft.Row([self.add_files, self.add_folder], spacing=SPACE)
        self.start = StartPanel(wording, on_add_files=on_add_files, on_add_folder=on_add_folder)
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
        self.editing = ft.Row([self.remove, self.clear, self.deselect], spacing=SPACE)
        self.controls: list[ft.Control] = [
            self.entry,
            self.start.control,
            self.inputs.control,
            self.editing,
        ]
        self.show_start(True)

    def show_start(self, empty: bool) -> None:
        """Nothing listed: the tiles alone. Something listed: the buttons, the list, its links."""
        self.start.control.visible = empty
        for control in (self.entry, self.inputs.control, self.editing):
            control.visible = not empty

    def remove_selected(self) -> None:
        chosen = self.inputs.selected()
        if chosen:
            self._on_remove(chosen)
