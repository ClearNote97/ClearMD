"""The logo mark and the app icon: one geometry, written as SVG and as PNG."""

from dataclasses import dataclass

from gui.drawing.canvas import CLEAR, CLEAR_BRIGHT, INK, TEAL, TEAL_BRIGHT, WHITE, _render, _rgba
from PIL import Image, ImageDraw

# --- The mark: the C embraces the M, whose right leg ends in an arrow (64 × 64 units) ------------

C_CENTER = (16.0, 36.0)
C_RADIUS = 9.0
C_FROM, C_TO = 60.0, 300.0  # degrees, clockwise from three o'clock (y down): open to the right
M_POINTS = [(29.0, 46.0), (29.0, 14.0), (41.0, 30.0), (53.0, 14.0), (53.0, 54.0)]
ARROW_POINTS = [(46.0, 47.0), (53.0, 54.0), (60.0, 47.0)]
MARK_STROKE = 5.5
APP_STROKE = 7.0  # thicker inside the app icon, where the mark is shrunk
APP_SCALE, APP_SHIFT = 0.72, 9.0  # the mark inside the rounded square

SVG_C = "M20.5 28.2A9 9 0 1 0 20.5 43.8"
SVG_M = "M29 46V14l12 16 12-16v40M46 47l7 7 7-7"


@dataclass(frozen=True)
class MarkColours:
    name: str
    c: str
    m: str


MARKS = (
    MarkColours("mark", CLEAR, TEAL),  # on light backgrounds
    MarkColours("mark-dark", CLEAR_BRIGHT, TEAL_BRIGHT),  # on dark backgrounds (the rail)
    MarkColours("mark-mono", INK, INK),
)
MARK_SIZES = (40, 256)
APP_SIZES = (16, 32, 48, 64, 128, 256)


def _stroke_line(
    draw: ImageDraw.ImageDraw, points: list[tuple[float, float]], width: float, colour: str
) -> None:
    """A polyline with round joins and round caps."""
    draw.line(points, fill=_rgba(colour), width=round(width), joint="curve")
    for x, y in (points[0], points[-1]):
        r = width / 2
        draw.ellipse((x - r, y - r, x + r, y + r), fill=_rgba(colour))


def _stroke_arc(
    draw: ImageDraw.ImageDraw,
    centre: tuple[float, float],
    radius: float,
    start: float,
    end: float,
    width: float,
    colour: str,
) -> None:
    """An arc whose stroke is centred on ``radius``, with round caps."""
    import math

    cx, cy = centre
    outer = radius + width / 2
    draw.arc(
        (cx - outer, cy - outer, cx + outer, cy + outer),
        start,
        end,
        fill=_rgba(colour),
        width=round(width),
    )
    for angle in (start, end):
        x = cx + radius * math.cos(math.radians(angle))
        y = cy + radius * math.sin(math.radians(angle))
        r = width / 2
        draw.ellipse((x - r, y - r, x + r, y + r), fill=_rgba(colour))


def _mark(
    draw: ImageDraw.ImageDraw,
    unit: float,
    shift: float,
    scale: float,
    stroke: float,
    c: str,
    m: str,
) -> None:
    """The mark in a 64-unit box, ``unit`` pixels per unit, moved and scaled as in the SVG."""

    def at(point: tuple[float, float]) -> tuple[float, float]:
        return ((shift + point[0] * scale) * unit, (shift + point[1] * scale) * unit)

    width = stroke * scale * unit
    centre = at(C_CENTER)
    _stroke_arc(draw, centre, C_RADIUS * scale * unit, C_FROM, C_TO, width, c)
    _stroke_line(draw, [at(p) for p in M_POINTS], width, m)
    _stroke_line(draw, [at(p) for p in ARROW_POINTS], width, m)


def mark_png(colours: MarkColours, size: int) -> Image.Image:
    return _render(
        size,
        lambda draw, px: _mark(draw, px / 64, 0.0, 1.0, MARK_STROKE, colours.c, colours.m),
    )


def app_png(size: int) -> Image.Image:
    def paint(draw: ImageDraw.ImageDraw, px: float) -> None:
        unit = px / 64
        draw.rounded_rectangle((2 * unit, 2 * unit, 62 * unit, 62 * unit), 15 * unit, _rgba(TEAL))
        _mark(draw, unit, APP_SHIFT, APP_SCALE, APP_STROKE, CLEAR_BRIGHT, WHITE)

    return _render(size, paint)


def mark_svg(colours: MarkColours) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" '
        'aria-label="ClearMD">\n'
        f'  <path d="{SVG_C}" stroke="{colours.c}" stroke-width="{MARK_STROKE}" '
        'stroke-linecap="round" fill="none"/>\n'
        f'  <path d="{SVG_M}" stroke="{colours.m}" stroke-width="{MARK_STROKE}" '
        'stroke-linecap="round" stroke-linejoin="round" fill="none"/>\n'
        "</svg>\n"
    )


def app_svg() -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" '
        'aria-label="ClearMD">\n'
        f'  <rect x="2" y="2" width="60" height="60" rx="15" fill="{TEAL}"/>\n'
        f'  <g transform="translate({APP_SHIFT:g} {APP_SHIFT:g}) scale({APP_SCALE:g})">\n'
        f'    <path d="{SVG_C}" stroke="{CLEAR_BRIGHT}" stroke-width="{APP_STROKE:g}" '
        'stroke-linecap="round" fill="none"/>\n'
        f'    <path d="{SVG_M}" stroke="{WHITE}" stroke-width="{APP_STROKE:g}" '
        'stroke-linecap="round" stroke-linejoin="round" fill="none"/>\n'
        "  </g>\n"
        "</svg>\n"
    )
