"""A row of choices that wraps when it does not fit (features 024, 028, 032): Split's three cuts,
Review's three answers about existing results. Each choice keeps its widgets on one line; the
choices go into as many aligned columns as the card has room for (all of them on one line when
they fit, two and one at 800 px, one per line at the narrowest)."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QSizePolicy, QWidget

from clearmd.frontend.design.metrics import GAP, SPACE


class FoldRow(QWidget):
    """``add`` one choice at a time; ``columns`` is how many sit side by side now."""

    def __init__(self) -> None:
        super().__init__()
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(SPACE)  # one spacing: the grid's rule; a choice keeps GAP after it
        self._items: list[QWidget] = []
        self.columns = 0
        # As narrow as the card: it wraps rather than widening the window.
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def add(self, *widgets: QWidget) -> None:
        item = QWidget()
        line = QHBoxLayout(item)
        line.setContentsMargins(0, 0, GAP - SPACE, 0)
        line.setSpacing(SPACE)
        for widget in widgets:
            line.addWidget(widget)
        line.addStretch(1)
        self._items.append(item)
        self.columns = 0
        self._place(len(self._items))

    @property
    def folded(self) -> bool:
        return self.columns < len(self._items)

    def _needed(self, columns: int) -> int:
        """The width ``columns`` aligned columns take: each as wide as its widest choice."""
        widths = [0] * columns
        for index, item in enumerate(self._items):
            widths[index % columns] = max(widths[index % columns], item.sizeHint().width())
        return sum(widths) + self._grid.spacing() * (columns - 1)

    def fit(self, width: int | None = None) -> None:
        """As many columns as fit in ``width`` (the row's own by default); at least one."""
        room = self.width() if width is None else width
        columns = next((n for n in range(len(self._items), 1, -1) if self._needed(n) <= room), 1)
        self._place(columns)

    def _place(self, columns: int) -> None:
        if columns == self.columns or not self._items:
            return
        self.columns = columns
        for item in self._items:
            self._grid.removeWidget(item)
        for index, item in enumerate(self._items):
            self._grid.addWidget(
                item, index // columns, index % columns, Qt.AlignmentFlag.AlignLeft
            )
        for column in range(len(self._items) + 1):
            self._grid.setColumnStretch(column, 1 if column == columns else 0)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 -- Qt's name
        self.fit(event.size().width())
        super().resizeEvent(event)
