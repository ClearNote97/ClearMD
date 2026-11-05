"""What the rail draws: the dimmed colour of a step and its numbered badge."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap

from clearmd.frontend.design.colors import blend
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.pyside.layout.units import BADGE


def rail_dim(palette: Palette) -> str:
    return blend(palette.rail_text, palette.rail, 0.55)


def badge(number: int, colour: str, fill: str) -> QPixmap:
    """A step's number in its circle, drawn at twice the size for sharp edges."""
    scale = 2
    pixmap = QPixmap(BADGE * scale, BADGE * scale)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = painter.pen()
    pen.setColor(QColor(colour))
    pen.setWidthF(1.5 * scale)
    painter.setPen(pen)
    painter.setBrush(QColor(fill))
    margin = scale
    painter.drawEllipse(QRectF(margin, margin, (BADGE - 2) * scale, (BADGE - 2) * scale))
    font = painter.font()
    font.setPixelSize(13 * scale)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, str(number))
    painter.end()
    pixmap.setDevicePixelRatio(scale)
    return pixmap
