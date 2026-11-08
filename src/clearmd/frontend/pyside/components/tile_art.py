"""What the start screen's tiles draw (features 023, 026, 032): the tools' icons of
``design.tool_art``, the same in the three windows, painted with Qt at twice the size."""

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap

from clearmd.frontend.design.tool_art import GRID, STROKE, Circle, Cubic, Shape, shapes

SCALE = 2  # drawn at twice the size for sharp edges


def _path(shape: Shape, unit: float) -> QPainterPath:
    def at(point: tuple[float, float]) -> QPointF:
        return QPointF(point[0] * unit, point[1] * unit)

    if isinstance(shape, Circle):
        path = QPainterPath()
        path.addEllipse(at(shape.centre), shape.radius * unit, shape.radius * unit)
        return path
    if isinstance(shape, Cubic):
        path = QPainterPath(at(shape.start))
        path.cubicTo(at(shape.c1), at(shape.c2), at(shape.end))
        return path
    first, *rest = shape.points
    path = QPainterPath(at(first))
    for point in rest:
        path.lineTo(at(point))
    if shape.closed:
        path.closeSubpath()
    return path


def tool_art(tool: str, size: int, colour: str) -> QPixmap:
    """The icon of ``tool`` ("convert", "split", "merge"), ``size`` pixels square."""
    pixmap = QPixmap(size * SCALE, size * SCALE)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    unit = size * SCALE / GRID
    pen = QPen(QColor(colour), STROKE * unit)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for shape in shapes(tool):
        painter.drawPath(_path(shape, unit))
    painter.end()
    pixmap.setDevicePixelRatio(SCALE)
    return pixmap
