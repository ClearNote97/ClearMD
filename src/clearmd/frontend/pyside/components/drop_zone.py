"""The drop zone: where files and folders can be dropped; a click adds files."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.pyside.components.primitives import label


class DropZone(QFrame):
    """Where files and folders can be dropped (the whole window takes them); a click adds files."""

    def __init__(self, *, on_click: Callable[[], None]) -> None:
        super().__init__()
        self.setObjectName("drop")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._on_click = on_click
        layout = QHBoxLayout(self)
        layout.setContentsMargins(GAP, SPACE, GAP, SPACE)
        layout.setSpacing(SPACE)
        self.text = label("dropText", wrap=True)  # two lines rather than squeezing the buttons
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.text)

    def show_text(self, text: str) -> None:
        self.text.setText(f"↓  {text}")

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802 -- Qt's name
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_click()
        super().mouseReleaseEvent(event)
