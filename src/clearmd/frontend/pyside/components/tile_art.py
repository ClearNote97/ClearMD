"""What the start screen's tiles draw (features 023, 026): a Markdown document, a pair of
scissors and two arrows joining into one, in lines of one colour, on a 24-unit grid like the rail's
badges."""

from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap

SCALE = 2  # drawn at twice the size for sharp edges
STROKE = 1.6  # in grid units


def _art(size: int, colour: str, draw: Callable[[QPainter, float], None]) -> QPixmap:
    pixmap = QPixmap(size * SCALE, size * SCALE)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    unit = size * SCALE / 24
    pen = QPen(QColor(colour), STROKE * unit)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    draw(painter, unit)
    painter.end()
    pixmap.setDevicePixelRatio(SCALE)
    return pixmap


def _document(painter: QPainter, u: float) -> None:
    """A page with its corner folded, and an M with a down arrow: Markdown's own mark."""
    page = QPainterPath(QPointF(5 * u, 3 * u))
    for x, y in ((14 * u, 3 * u), (19 * u, 8 * u), (19 * u, 21 * u), (5 * u, 21 * u)):
        page.lineTo(x, y)
    page.closeSubpath()
    painter.drawPath(page)
    corner = QPainterPath(QPointF(14 * u, 3 * u))
    corner.lineTo(14 * u, 8 * u)
    corner.lineTo(19 * u, 8 * u)
    painter.drawPath(corner)
    mark = QPainterPath(QPointF(7.5 * u, 17 * u))
    for x, y in ((7.5 * u, 11.5 * u), (10 * u, 14 * u), (12.5 * u, 11.5 * u), (12.5 * u, 17 * u)):
        mark.lineTo(x, y)
    painter.drawPath(mark)
    painter.drawLine(QPointF(15.5 * u, 11.5 * u), QPointF(15.5 * u, 17 * u))
    arrow = QPainterPath(QPointF(14 * u, 15.5 * u))
    arrow.lineTo(15.5 * u, 17 * u)
    arrow.lineTo(17 * u, 15.5 * u)
    painter.drawPath(arrow)


def _scissors(painter: QPainter, u: float) -> None:
    """Two handles and two blades crossing: the cut."""
    painter.drawEllipse(QRectF(3 * u, 14 * u, 6 * u, 6 * u))
    painter.drawEllipse(QRectF(15 * u, 14 * u, 6 * u, 6 * u))
    painter.drawLine(QPointF(8 * u, 15 * u), QPointF(17 * u, 3 * u))
    painter.drawLine(QPointF(16 * u, 15 * u), QPointF(7 * u, 3 * u))


def _merge(painter: QPainter, u: float) -> None:
    """Two paths coming together into one, with its arrow head: several documents into one."""
    for start in (3 * u, 21 * u):
        path = QPainterPath(QPointF(start, 3 * u))
        path.cubicTo(QPointF(start, 11 * u), QPointF(12 * u, 9 * u), QPointF(12 * u, 15 * u))
        painter.drawPath(path)
    painter.drawLine(QPointF(12 * u, 15 * u), QPointF(12 * u, 21 * u))
    head = QPainterPath(QPointF(8.5 * u, 17.5 * u))
    head.lineTo(12 * u, 21 * u)
    head.lineTo(15.5 * u, 17.5 * u)
    painter.drawPath(head)


def document_art(size: int, colour: str) -> QPixmap:
    return _art(size, colour, _document)


def scissors_art(size: int, colour: str) -> QPixmap:
    return _art(size, colour, _scissors)


def merge_art(size: int, colour: str) -> QPixmap:
    return _art(size, colour, _merge)
