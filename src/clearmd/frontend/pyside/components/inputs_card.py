"""The Choose step's input half: Add files / Add folder, the drop zone, the numbered list and the
editing links. It adds its widgets to the step's own layout, so the arrangement stays the step's."""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QRadioButton, QVBoxLayout

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.pyside.components.drop_zone import DropZone
from clearmd.frontend.pyside.components.file_list import FileList
from clearmd.frontend.pyside.components.primitives import button


class InputsCard:
    """Add files / Add folder and the drop zone, the numbered list, the editing links."""

    def __init__(
        self,
        layout: QVBoxLayout,
        *,
        text: Callable[[QLabel | QPushButton | QRadioButton, str], None],
        on_add_files: Callable[[], None],
        on_add_folder: Callable[[], None],
        on_remove: Callable[[list[Path]], None],
        on_clear: Callable[[], None],
    ) -> None:
        self._on_remove = on_remove
        entry = QHBoxLayout()
        entry.setSpacing(GAP)
        self._buttons = QVBoxLayout()
        self._buttons.setSpacing(SPACE)
        self.add_files = button("", on_add_files)
        self.add_folder = button("", on_add_folder)
        text(self.add_files, "gui.main.add_files")
        text(self.add_folder, "gui.main.add_folder")
        self._buttons.addWidget(self.add_files)
        self._buttons.addWidget(self.add_folder)
        entry.addLayout(self._buttons)
        self.drop_zone = DropZone(on_click=on_add_files)
        entry.addWidget(self.drop_zone, 1)
        layout.addLayout(entry)
        self._short = False

        self.inputs = FileList(1, checks=True, widths=(320,))
        self.inputs.tree.setAccessibleName("inputs")
        layout.addWidget(self.inputs, 1)

        editing = QHBoxLayout()
        editing.setSpacing(SPACE)
        self.remove = button("link", self._remove_selected)
        self.clear = button("link", on_clear)
        self.deselect = button("link", self.inputs.clear_selection)
        for widget, key in (
            (self.remove, "gui.main.remove"),
            (self.clear, "gui.main.clear"),
            (self.deselect, "gui.main.deselect"),
        ):
            text(widget, key)
            editing.addWidget(widget)
        editing.addStretch(1)
        layout.addLayout(editing)

    def set_short(self, short: bool) -> None:
        """A short window: the add buttons side by side, so the list keeps its rows (011)."""
        if short == self._short:
            return
        self._short = short
        self._buttons.setDirection(
            QVBoxLayout.Direction.LeftToRight if short else QVBoxLayout.Direction.TopToBottom
        )

    def _remove_selected(self) -> None:
        chosen = self.inputs.selected()
        if chosen:
            self._on_remove(chosen)
