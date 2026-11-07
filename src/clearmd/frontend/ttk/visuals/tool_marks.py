"""Pillow marks of the tools (feature 023): a document for Convert, scissors for Split, and the
house of the rail's Home. Drawn in one colour, larger and reduced, like the rail's art."""

from PIL import Image, ImageDraw

from clearmd.frontend.ttk.visuals.shapes import SUPERSAMPLE, rgba

TOOL_ICON = 40  # a tile's icon (as flet's: 5 x SPACE)


def _canvas(size: int) -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
    s = SUPERSAMPLE * 2
    big = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    return big, ImageDraw.Draw(big), s


def _small(big: Image.Image, size: int) -> Image.Image:
    return big.resize((size, size), Image.Resampling.LANCZOS)


def document(colour: str, size: int = TOOL_ICON) -> Image.Image:
    """An outlined page with a folded corner and three lines of text (Convert to Markdown)."""
    big, draw, s = _canvas(size)
    u = size * s / 40  # one unit of a 40 x 40 drawing
    ink = rgba(colour)
    width = round(2.6 * u)
    left, top, right, bottom, fold = 9 * u, 5 * u, 31 * u, 35 * u, 8 * u
    outline = [
        (left, top), (right - fold, top), (right, top + fold), (right, bottom),
        (left, bottom), (left, top),
    ]  # fmt: skip
    draw.line(outline, fill=ink, width=width, joint="curve")
    draw.line([(right - fold, top), (right - fold, top + fold), (right, top + fold)],
              fill=ink, width=width, joint="curve")  # fmt: skip
    for y, end in ((19 * u, 26 * u), (24.5 * u, 26 * u), (30 * u, 21 * u)):
        draw.line([(14 * u, y), (end, y)], fill=ink, width=round(2.2 * u))
    return _small(big, size)


def scissors(colour: str, size: int = TOOL_ICON) -> Image.Image:
    """Open scissors: two round handles below, the blades crossing above them (Split a PDF)."""
    big, draw, s = _canvas(size)
    u = size * s / 40
    ink = rgba(colour)
    width = round(2.6 * u)
    radius = 5 * u
    for cx in (12 * u, 28 * u):
        cy = 29 * u
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=ink,
                     width=width)  # fmt: skip
    # Each blade leaves its handle and crosses the other at the pivot.
    draw.line([(15.5 * u, 25 * u), (29 * u, 5 * u)], fill=ink, width=width)
    draw.line([(24.5 * u, 25 * u), (11 * u, 5 * u)], fill=ink, width=width)
    pivot = 1.6 * u
    draw.ellipse((20 * u - pivot, 18.3 * u - pivot, 20 * u + pivot, 18.3 * u + pivot), fill=ink)
    return _small(big, size)


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
