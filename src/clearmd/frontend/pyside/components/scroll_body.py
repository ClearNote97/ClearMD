"""A dialog's body that scrolls when the screen is shorter than it (audit v3, F3-01): it asks for
its whole content's height, so the dialog opens as tall as it needs where there is room, and
shrinks under the screen's height with a scroll bar where there is not."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget

from clearmd.frontend.design.metrics import SPACE


class ScrollBody(QScrollArea):
    """``rows`` is the layout to fill; the foot stays outside, always visible."""

    def __init__(self) -> None:
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        self.rows = QVBoxLayout(content)
        self.rows.setContentsMargins(0, 0, SPACE, 0)  # room for the scroll bar
        self.setWidget(content)

    def sizeHint(self) -> QSize:  # noqa: N802 -- Qt's name
        """The whole content, its wrapped lines at the area's width: no scroll bar if it fits."""
        hint = super().sizeHint()
        width = max(self.viewport().width(), 1)
        hint.setHeight(self.rows.totalHeightForWidth(width))
        return hint

    def minimumSizeHint(self) -> QSize:  # noqa: N802 -- Qt's name
        return QSize(super().minimumSizeHint().width(), 8 * SPACE)

    def hasHeightForWidth(self) -> bool:  # noqa: N802 -- Qt's name
        return True

    def heightForWidth(self, width: int) -> int:  # noqa: N802 -- Qt's name
        return self.rows.totalHeightForWidth(max(width - SPACE, 1))
