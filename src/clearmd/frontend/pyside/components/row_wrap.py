"""A list whose rows show their whole text, wrapped on as many lines as it takes (audit v4, F3-01,
F5-01): the reason and what to do are never cut with "…" nor only in a tooltip. Qt's tree does not
size wrapped rows by itself, so each row's height is measured from its columns' widths, again when
a column or the list changes width."""

from PySide6.QtCore import QEvent, QObject, QRect, QSize, Qt, QTimer
from PySide6.QtWidgets import QTreeWidget

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.pyside.layout.units import ROW_HEIGHT

TEXT_MARGIN = SPACE  # the item's text margins, left and right together, and some room


class RowWrap(QObject):
    """Sets each row's height for its wrapped text; ``fit`` after the rows change."""

    def __init__(self, tree: QTreeWidget) -> None:
        super().__init__(tree)
        self._tree = tree
        tree.setWordWrap(True)
        tree.setUniformRowHeights(False)
        tree.setTextElideMode(Qt.TextElideMode.ElideNone)
        self._later = QTimer(self)
        self._later.setSingleShot(True)
        self._later.timeout.connect(self.fit)
        tree.header().sectionResized.connect(lambda *_: self._later.start(0))
        tree.viewport().installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802 -- Qt's name
        if event.type() is QEvent.Type.Resize:
            self._later.start(0)
        return super().eventFilter(watched, event)

    def fit(self) -> None:
        tree, header = self._tree, self._tree.header()
        metrics = tree.fontMetrics()
        flags = Qt.TextFlag.TextWordWrap
        for index in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(index)
            if item is None:
                continue
            height = ROW_HEIGHT
            for column in range(1, tree.columnCount()):
                width = header.sectionSize(column) - TEXT_MARGIN - (SPACE * 3 if column == 1 else 0)
                if width <= 0 or not item.text(column):
                    continue
                box = metrics.boundingRect(QRect(0, 0, width, 100_000), flags, item.text(column))
                height = max(height, box.height() + SPACE)
            last = tree.columnCount() - 1
            if item.sizeHint(last).height() != height:
                item.setSizeHint(last, QSize(header.sectionSize(last), height))
