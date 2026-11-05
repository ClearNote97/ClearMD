"""The working area (ADR-0027): its soft shape at the top right and the header (step, title,
subtitle); the page goes in ``body``."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QVBoxLayout, QWidget

from clearmd.frontend.design.metrics import GAP, HALF, SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.pyside.components.primitives import label


class Surface(QWidget):
    """The working area: its soft shape at the top right, the header (step, title, subtitle)."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ground")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._shape = QColor("#D7EEEA")
        layout = QVBoxLayout(self)
        # The window's own margin is the gutter above and below: the page ends where the rail ends.
        layout.setContentsMargins(GAP, 0, GAP, 0)
        layout.setSpacing(HALF)
        self.eyebrow = label("eyebrow")
        self.title = label("title")
        self.subtitle = label("subtitle", wrap=True)
        for widget in (self.eyebrow, self.title, self.subtitle):
            layout.addWidget(widget)
        layout.addSpacing(SPACE)
        self.body = QVBoxLayout()
        self.body.setSpacing(0)
        layout.addLayout(self.body, 1)

    def apply_palette(self, palette: Palette) -> None:
        self._shape = QColor(palette.shape)
        self.update()

    def show_header(self, *, eyebrow: str, title: str, subtitle: str) -> None:
        self.eyebrow.setText(eyebrow)
        self.title.setText(title)
        self.subtitle.setText(subtitle)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 -- Qt's name
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._shape)
        width = self.width()
        painter.drawEllipse(QRectF(width - 380, -260, 640, 360))
        painter.drawEllipse(QRectF(width - 560, -300, 380, 360))
        painter.end()
        super().paintEvent(event)
