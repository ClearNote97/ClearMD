"""Pillow marks of the tools: the start screen's icons from ``design.tool_art`` (the same shapes
in the three windows, feature 032) and the house of the rail's Home. Drawn in one colour, larger
and reduced, like the rail's art."""

from PIL import Image, ImageDraw

from clearmd.frontend.design import tool_art
from clearmd.frontend.ttk.visuals.shapes import SUPERSAMPLE, rgba

TOOL_ICON = 40  # a tile's icon (as flet's: 5 x SPACE)


def _canvas(size: int) -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
    s = SUPERSAMPLE * 2
    big = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    return big, ImageDraw.Draw(big), s


def _small(big: Image.Image, size: int) -> Image.Image:
    return big.resize((size, size), Image.Resampling.LANCZOS)


def tool_icon(tool: str, colour: str, size: int = TOOL_ICON) -> Image.Image:
    """The start screen's icon of ``tool`` (feature 032, AC-04): the shapes of
    ``design.tool_art``, the same in the three windows, drawn with Pillow in one colour, with
    round caps and joins."""
    big, draw, s = _canvas(size)
    scale = size * s / tool_art.GRID
    ink = rgba(colour)
    width = max(1, round(tool_art.STROKE * scale))
    cap = width / 2

    def at(point: tool_art.Point) -> tuple[float, float]:
        return point[0] * scale, point[1] * scale

    for shape in tool_art.shapes(tool):
        if isinstance(shape, tool_art.Circle):
            (x, y), r = at(shape.centre), shape.radius * scale
            draw.ellipse((x - r - cap, y - r - cap, x + r + cap, y + r + cap), outline=ink,
                         width=width)  # fmt: skip
            continue
        if isinstance(shape, tool_art.Cubic):
            points = [at(point) for point in tool_art.flatten(shape)]
        else:
            points = [at(point) for point in shape.points]
            if shape.closed:
                points.append(points[0])
        draw.line(points, fill=ink, width=width, joint="curve")
        for x, y in points:  # round caps (Pillow draws square ends)
            draw.ellipse((x - cap, y - cap, x + cap, y + cap), fill=ink)
    return _small(big, size)


def document(colour: str, size: int = TOOL_ICON) -> Image.Image:
    """Convert to Markdown: a page with its corner folded and Markdown's mark."""
    return tool_icon("convert", colour, size)


def scissors(colour: str, size: int = TOOL_ICON) -> Image.Image:
    """Split a Document: a pair of scissors."""
    return tool_icon("split", colour, size)


def merge(colour: str, size: int = TOOL_ICON) -> Image.Image:
    """Merge Documents: two paths joining into one."""
    return tool_icon("merge", colour, size)


def house(colour: str, size: int) -> Image.Image:
    """A small house: the rail's Home, in its circle."""
    big, draw, s = _canvas(size)
    u = size * s / 16
    ink = rgba(colour)
    width = round(1.5 * u)
    draw.line([(2.5 * u, 8 * u), (8 * u, 3 * u), (13.5 * u, 8 * u)], fill=ink, width=width,
              joint="curve")  # fmt: skip
    draw.line([(4.5 * u, 7 * u), (4.5 * u, 13 * u), (11.5 * u, 13 * u), (11.5 * u, 7 * u)],
              fill=ink, width=width, joint="curve")  # fmt: skip
    return _small(big, size)
