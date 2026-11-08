"""A numbered list of files (ADR-0027): ``#``, the file's icon and name, the extra columns, a
message in place of an empty list; optionally a box on each row."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QStackedLayout,
    QTreeWidget,
    QTreeWidgetItem,
)

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.pyside.components.primitives import card, label
from clearmd.frontend.pyside.layout.units import ICON, LIST_HEADER, ROW_HEIGHT
from clearmd.frontend.pyside.visuals.images import icon


@dataclass(frozen=True)
class ListRow:
    icon: str
    name: str
    values: tuple[str, ...]  # one per extra column
    warning: bool = False  # drawn in the warning colour
    payload: Any = None  # what the row stands for (a path), returned by ``selected``


class _Tree(QTreeWidget):
    """A tree that can ask for a number of rows only (``rows``): its preferred height."""

    rows = 0

    def sizeHint(self) -> QSize:  # noqa: N802 -- Qt's name
        hint = super().sizeHint()
        if self.rows:
            hint.setHeight(LIST_HEADER + self.rows * ROW_HEIGHT + 2 * SPACE)
        return hint

    def minimumSizeHint(self) -> QSize:  # noqa: N802 -- Qt's name
        return self.sizeHint() if self.rows else super().minimumSizeHint()


class FileList(QFrame):
    """``#``, the file's icon and name, then the extra columns; a message in place of an empty
    list. ``checks``: a box on each row, for a list whose selection does something (Choose's
    Remove selected); a list to read has none (feature 014)."""

    selection_changed = Signal()

    def __init__(self, columns: int, *, checks: bool = False, widths: Sequence[int] = ()) -> None:
        super().__init__()
        self.checks = checks
        self._rows: tuple[ListRow, ...] = ()
        self._warning = QColor("#B45309")
        self._stack = QStackedLayout(self)
        self._stack.setContentsMargins(0, 0, 0, 0)  # Qt's default is off the grid
        self.tree = _Tree()
        self.tree.setColumnCount(2 + columns)
        self.tree.setRootIsDecorated(False)
        self.tree.setUniformRowHeights(True)
        self.tree.setIconSize(QSize(ICON, ICON))
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        header = self.tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tree.setColumnWidth(0, 7 * SPACE if checks else 5 * SPACE)
        for column, width in enumerate(widths, start=1):
            self.tree.setColumnWidth(column, width)
        self.tree.itemSelectionChanged.connect(self._selection_changed)
        self.tree.itemChanged.connect(self._checked)
        self._stack.addWidget(self.tree)
        self.empty = label("empty", wrap=True)
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        holder, holder_layout = card()
        holder_layout.addWidget(self.empty)
        self._stack.addWidget(holder)
        self._syncing = False
        self._stack.setCurrentIndex(1)

    def apply_headings(self, headings: Sequence[str], empty: str) -> None:
        self.tree.setHeaderLabels(["#", *headings])
        self.empty.setText(empty)
        self._stack.setCurrentIndex(0 if self._rows or not empty else 1)

    def apply_palette(self, palette: Palette) -> None:
        self._warning = QColor(palette.warning)
        for index, row in enumerate(self._rows):  # recoloured in place: the selection stays
            item = self.tree.topLevelItem(index)
            if item is None or not row.warning:
                continue
            for column in range(1, 2 + len(row.values)):
                item.setForeground(column, self._warning)

    def show_rows(self, rows: Sequence[ListRow]) -> None:
        self._rows = tuple(rows)
        self._syncing = True
        self.tree.clear()
        for number, row in enumerate(self._rows, start=1):
            item = QTreeWidgetItem([str(number), row.name, *row.values])
            item.setIcon(1, icon(row.icon))
            item.setData(0, Qt.ItemDataRole.UserRole, number - 1)
            if self.checks:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(0, Qt.CheckState.Unchecked)
            for column in range(1, 2 + len(row.values)):
                item.setToolTip(column, item.text(column))
                if row.warning:
                    item.setForeground(column, self._warning)
            self.tree.addTopLevelItem(item)
        self._syncing = False
        self._stack.setCurrentIndex(0 if self._rows or not self.empty.text() else 1)

    def ask_rows(self, rows: int) -> None:
        """Ask for ``rows`` rows under the header, at the least and no more: the list takes the
        room left over (feature 032: step 1 at 800 x 600)."""
        self.tree.rows = rows
        self.tree.updateGeometry()

    def rows(self) -> tuple[ListRow, ...]:
        return self._rows

    def selected_rows(self) -> list[ListRow]:
        indexes = sorted(
            int(item.data(0, Qt.ItemDataRole.UserRole)) for item in self.tree.selectedItems()
        )
        return [self._rows[index] for index in indexes]

    def selected(self) -> list[Any]:
        """What the selected rows stand for (their payloads)."""
        return [row.payload for row in self.selected_rows()]

    def current(self) -> ListRow | None:
        chosen = self.selected_rows()
        return chosen[0] if chosen else None

    def select(self, index: int) -> None:
        item = self.tree.topLevelItem(index)
        if item is not None:
            self.tree.setCurrentItem(item)

    def clear_selection(self) -> None:
        self.tree.clearSelection()

    def _selection_changed(self) -> None:
        """The boxes follow the selection (feature 007)."""
        if self.checks:
            self._syncing = True
            for index in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(index)
                if item is not None:
                    state = Qt.CheckState.Checked if item.isSelected() else Qt.CheckState.Unchecked
                    item.setCheckState(0, state)
            self._syncing = False
        self.selection_changed.emit()

    def _checked(self, item: QTreeWidgetItem, column: int) -> None:
        """A box clicked: its row joins or leaves the selection."""
        if self._syncing or column != 0:
            return
        item.setSelected(item.checkState(0) == Qt.CheckState.Checked)
