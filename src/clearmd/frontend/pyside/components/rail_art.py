"""What the rail draws: the dimmed colour of a step, its numbered badge and Home's house."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap, QPolygonF

from clearmd.frontend.design.colors import blend
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.pyside.layout.units import BADGE

SCALE = 2  # drawn at twice the size for sharp edges


def rail_dim(palette: Palette) -> str:
    return blend(palette.rail_text, palette.rail, 0.55)


def _circle(colour: str, fill: str) -> tuple[QPixmap, QPainter]:
    """A badge's circle, and the painter left open to draw what goes in it."""
    pixmap = QPixmap(BADGE * SCALE, BADGE * SCALE)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = painter.pen()
    pen.setColor(QColor(colour))
    pen.setWidthF(1.5 * SCALE)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(QColor(fill))
    painter.drawEllipse(QRectF(SCALE, SCALE, (BADGE - 2) * SCALE, (BADGE - 2) * SCALE))
    return pixmap, painter


def _done(pixmap: QPixmap, painter: QPainter) -> QPixmap:
    painter.end()
    pixmap.setDevicePixelRatio(SCALE)
    return pixmap


def badge(number: int, colour: str, fill: str) -> QPixmap:
    """A step's number in its circle."""
    pixmap, painter = _circle(colour, fill)
    font = painter.font()
    font.setPixelSize(13 * SCALE)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, str(number))
    return _done(pixmap, painter)


def home_badge(colour: str, fill: str) -> QPixmap:
    """Home's mark in the same circle as a step's number: a small house (feature 023)."""
    pixmap, painter = _circle(colour, fill)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    unit = BADGE * SCALE / 24  # drawn on a 24-unit grid
    roof = (
        QPointF(7 * unit, 12 * unit),
        QPointF(12 * unit, 7.5 * unit),
        QPointF(17 * unit, 12 * unit),
    )
    painter.drawPolyline(QPolygonF(list(roof)))
    painter.drawRect(QRectF(8.5 * unit, 11.5 * unit, 7 * unit, 5.5 * unit))
    return _done(pixmap, painter)
