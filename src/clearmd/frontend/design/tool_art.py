"""The start screen's three icons (feature 032, AC-04) as plain data, so the three windows draw the
very same pictures: Convert is a Markdown document, Split a pair of scissors, Merge two paths
joining into one. Lines of one colour on a 24-unit grid, round caps and joins, no fill.

Each toolkit renders the shapes in its own way (Qt's painter, Pillow, an SVG for flet: ``svg``).
No toolkit is imported here."""

from collections.abc import Sequence
from dataclasses import dataclass
from html import escape

GRID = 24  # the icon's side, in units
STROKE = 1.6  # the lines' width, in units

Point = tuple[float, float]


@dataclass(frozen=True)
class Polyline:
    """Straight segments through ``points``; ``closed`` joins the last to the first."""

    points: tuple[Point, ...]
    closed: bool = False


@dataclass(frozen=True)
class Circle:
    centre: Point
    radius: float


@dataclass(frozen=True)
class Cubic:
    """A cubic Bézier curve from ``start`` to ``end``, pulled towards ``c1`` and ``c2``."""

    start: Point
    c1: Point
    c2: Point
    end: Point


Shape = Polyline | Circle | Cubic

DOCUMENT: tuple[Shape, ...] = (  # a page with its corner folded, and Markdown's "M↓"
    Polyline(((5, 3), (14, 3), (19, 8), (19, 21), (5, 21)), closed=True),
    Polyline(((14, 3), (14, 8), (19, 8))),
    Polyline(((7.5, 17), (7.5, 11.5), (10, 14), (12.5, 11.5), (12.5, 17))),
    Polyline(((15.5, 11.5), (15.5, 17))),
    Polyline(((14, 15.5), (15.5, 17), (17, 15.5))),
)
SCISSORS: tuple[Shape, ...] = (  # two handles and two blades crossing
    Circle((6, 17), 3),
    Circle((18, 17), 3),
    Polyline(((8, 15), (17, 3))),
    Polyline(((16, 15), (7, 3))),
)
MERGE: tuple[Shape, ...] = (  # two paths coming together into one, with its arrow head
    Cubic((3, 3), (3, 11), (12, 9), (12, 15)),
    Cubic((21, 3), (21, 11), (12, 9), (12, 15)),
    Polyline(((12, 15), (12, 21))),
    Polyline(((8.5, 17.5), (12, 21), (15.5, 17.5))),
)
ART: dict[str, tuple[Shape, ...]] = {"convert": DOCUMENT, "split": SCISSORS, "merge": MERGE}


def shapes(tool: str) -> tuple[Shape, ...]:
    """The icon of ``tool`` ("convert", "split", "merge"; the presenter's ``Tool`` values)."""
    return ART[str(tool)]


def flatten(curve: Cubic, steps: int = 16) -> tuple[Point, ...]:
    """The curve as ``steps`` straight segments, for a toolkit that draws no curves (Pillow)."""
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = curve.start, curve.c1, curve.c2, curve.end
    points = []
    for index in range(steps + 1):
        t = index / steps
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t**2, t**3
        points.append((a * x0 + b * x1 + c * x2 + d * x3, a * y0 + b * y1 + c * y2 + d * y3))
    return tuple(points)


def _number(value: float) -> str:
    return f"{value:g}"


def _pairs(points: Sequence[Point]) -> str:
    return " ".join(f"{_number(x)},{_number(y)}" for x, y in points)


def _element(shape: Shape) -> str:
    if isinstance(shape, Circle):
        (x, y), r = shape.centre, shape.radius
        return f'<circle cx="{_number(x)}" cy="{_number(y)}" r="{_number(r)}"/>'
    if isinstance(shape, Cubic):
        start, rest = _pairs((shape.start,)), _pairs((shape.c1, shape.c2, shape.end))
        return f'<path d="M{start} C{rest}"/>'
    tag = "polygon" if shape.closed else "polyline"
    return f'<{tag} points="{_pairs(shape.points)}"/>'


def svg(tool: str, colour: str, size: int) -> str:
    """The icon as SVG text, ``size`` pixels square, its lines in ``colour``."""
    body = "".join(_element(shape) for shape in shapes(tool))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {GRID} {GRID}" fill="none" stroke="{escape(colour, quote=True)}" '
        f'stroke-width="{_number(STROKE)}" stroke-linecap="round" stroke-linejoin="round">'
        f"{body}</svg>"
    )
