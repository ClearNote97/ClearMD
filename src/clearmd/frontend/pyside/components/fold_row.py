"""A row of choices that folds into a column when it does not fit (features 024, 028): Split's
three cuts, Review's three answers about existing results."""

from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QBoxLayout, QHBoxLayout, QSizePolicy, QWidget

from clearmd.frontend.design.metrics import GAP, SPACE


class FoldRow(QWidget):
    """Choices side by side; one under the other when the card is narrower than they are (a
    compact window, longer words), so none is cut off. Each ``add`` is one choice: its widgets
    stay together on one line."""

    def __init__(self) -> None:
        super().__init__()
        self._layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(GAP)
        self._layout.addStretch(1)
        self._items: list[QWidget] = []
        # As narrow as the card: it folds rather than widening the window.
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def add(self, *widgets: QWidget) -> None:
        item = QWidget()
        line = QHBoxLayout(item)
        line.setContentsMargins(0, 0, 0, 0)
        line.setSpacing(SPACE)
        for widget in widgets:
            line.addWidget(widget)
        line.addStretch(1)
        self._layout.insertWidget(len(self._items), item)
        self._items.append(item)

    @property
    def folded(self) -> bool:
        return self._layout.direction() is QBoxLayout.Direction.TopToBottom

    def fit(self, width: int | None = None) -> None:
        """Side by side if they fit in ``width`` (the row's own by default), else folded."""
        needed = sum(item.sizeHint().width() for item in self._items)
        needed += self._layout.spacing() * (len(self._items) - 1)
        room = self.width() if width is None else width
        direction = QBoxLayout.Direction
        wanted = direction.TopToBottom if room < needed else direction.LeftToRight
        if wanted is not self._layout.direction():
            self._layout.setDirection(wanted)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 -- Qt's name
        self.fit(event.size().width())
        super().resizeEvent(event)
