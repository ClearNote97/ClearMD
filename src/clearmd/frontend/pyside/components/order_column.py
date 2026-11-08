"""Merge's order on step 1's list (feature 032): ▲ and ▼ on each row, in a column of their own,
shown only for Merge. Each moves its document one place; the first cannot go up, the last cannot
go down (the presenter says which can, per row). After a move the keyboard stays on the arrow
just pressed, now on the document's new row."""

from collections.abc import Callable, Sequence
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QHeaderView, QPushButton, QTreeWidget, QWidget

from clearmd.frontend.design.metrics import HALF
from clearmd.frontend.presenter.models import InputRow
from clearmd.frontend.pyside.components.primitives import button

ARROW = 28  # an arrow's square: inside a row of the list (36 px)
UP, DOWN = -1, +1


class OrderColumn:
    """The arrows of ``tree``'s rows, in a column after the others."""

    def __init__(self, tree: QTreeWidget, on_move: Callable[[Path, int], None]) -> None:
        self._tree = tree
        self._on_move = on_move
        self.column = tree.columnCount()
        tree.setColumnCount(self.column + 1)
        tree.setColumnWidth(self.column, 2 * ARROW + 3 * HALF)
        tree.setColumnHidden(self.column, True)
        self._words = {UP: "", DOWN: ""}
        self._pressed: tuple[Path, int] | None = None
        self.arrows: list[dict[int, QPushButton]] = []  # per row, by direction (for tests)

    def show(self, rows: Sequence[InputRow], *, merge: bool) -> None:
        """The arrows of ``rows`` (the list's own rows, in order); none outside Merge."""
        self._tree.setColumnHidden(self.column, not merge)
        header = self._tree.headerItem()
        if header is not None:
            header.setText(self.column, "")  # the arrows speak for themselves (tooltips)
        # With the arrows, the folder column takes the room left and the arrows keep theirs.
        sections = self._tree.header()
        sections.setStretchLastSection(not merge)
        stretch = QHeaderView.ResizeMode.Stretch if merge else QHeaderView.ResizeMode.Interactive
        sections.setSectionResizeMode(self.column - 1, stretch)
        sections.setSectionResizeMode(self.column, QHeaderView.ResizeMode.Fixed)
        self.arrows = []
        for index, row in enumerate(rows):
            item = self._tree.topLevelItem(index)
            if item is None:
                continue
            if not merge:
                self._tree.removeItemWidget(item, self.column)
                continue
            cell = QWidget()
            line = QHBoxLayout(cell)
            line.setContentsMargins(0, 0, 0, 0)
            line.setSpacing(HALF)
            arrows = {
                UP: self._arrow("▲", row.path, UP, row.up),
                DOWN: self._arrow("▼", row.path, DOWN, row.down),
            }
            for arrow in arrows.values():
                line.addWidget(arrow)
            line.addStretch(1)
            self._tree.setItemWidget(item, self.column, cell)
            self.arrows.append(arrows)
        self._refocus(rows)

    def apply_language(self, move_up: str, move_down: str) -> None:
        self._words = {UP: move_up, DOWN: move_down}
        for arrows in self.arrows:
            for direction, arrow in arrows.items():
                self._name(arrow, direction)

    def _arrow(self, glyph: str, path: Path, direction: int, enabled: bool) -> QPushButton:
        arrow = button("order", lambda: self._move(path, direction))
        arrow.setText(glyph)
        arrow.setFixedSize(ARROW, ARROW)
        arrow.setEnabled(enabled)
        arrow.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._name(arrow, direction)
        return arrow

    def _name(self, arrow: QPushButton, direction: int) -> None:
        arrow.setToolTip(self._words[direction])
        arrow.setAccessibleName(self._words[direction])

    def _move(self, path: Path, direction: int) -> None:
        self._pressed = (path, direction)
        self._on_move(path, direction)

    def _refocus(self, rows: Sequence[InputRow]) -> None:
        """The arrow just pressed, on its document's new row; the other one if it cannot move
        further that way."""
        pressed, self._pressed = self._pressed, None
        if pressed is None:
            return
        path, direction = pressed
        for index, row in enumerate(rows):
            if row.path == path and index < len(self.arrows):
                arrows = self.arrows[index]
                target = arrows[direction] if arrows[direction].isEnabled() else arrows[-direction]
                target.setFocus()
                return
