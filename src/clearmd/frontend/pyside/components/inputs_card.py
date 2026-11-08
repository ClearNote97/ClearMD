"""The Choose step's input half: Add files / Add folder, the drop zone, the numbered list (with
Merge's order, feature 032) and the editing links. It adds its widgets to the step's own layout,
so the arrangement stays the step's."""

from collections.abc import Callable, Sequence
from pathlib import Path

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QRadioButton, QVBoxLayout

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.presenter.models import InputRow
from clearmd.frontend.pyside.components.drop_zone import DropZone
from clearmd.frontend.pyside.components.file_list import FileList
from clearmd.frontend.pyside.components.order_column import OrderColumn
from clearmd.frontend.pyside.components.primitives import button, label
from clearmd.i18n import Catalog


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
        on_move: Callable[[Path, int], None],
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
        # Two rows under the header, at the least and as its wish: the list takes the room left,
        # and below that the step scrolls (032, 800 px).
        self.inputs.ask_rows(2)
        layout.addWidget(self.inputs, 1)
        self.order = OrderColumn(self.inputs.tree, on_move)
        self.order_hint = label("muted", wrap=True)  # Merge's, with two documents or more
        text(self.order_hint, "gui.main.order_hint")
        self.order_hint.hide()
        layout.addWidget(self.order_hint)

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

    def show_order(self, rows: Sequence[InputRow], *, merge: bool) -> None:
        """Merge's arrows on the list's rows and its hint; neither for Convert or Split."""
        self.order.show(rows, merge=merge)
        self.order_hint.setVisible(merge and len(rows) >= 2)

    def apply_language(self, catalog: Catalog) -> None:
        self.order.apply_language(
            catalog.text("gui.main.move_up"), catalog.text("gui.main.move_down")
        )

    def _remove_selected(self) -> None:
        chosen = self.inputs.selected()
        if chosen:
            self._on_remove(chosen)
