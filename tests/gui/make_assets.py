"""Draws ClearMD's logo and file icons (ADR-0027): one geometry, written as SVG and as PNG.

Run in the dev container (the icons' letters use its DejaVu Sans Bold):

    uv run python tests/gui/make_assets.py

``tests/unit/frontend/test_assets.py`` checks that the committed files match what this draws.
"""

import io
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parents[2] / "src" / "clearmd" / "frontend" / "assets"
FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
# The dev container's DejaVu Sans Bold (Debian 12): another version draws the letters differently.
FONT_SHA256 = "0d977336a6d5fba34eab8e3199eb218327161b5143749f802982c2bc34df0c96"
SUPERSAMPLE = 8  # drawn this many times larger, then reduced: smooth edges

TEAL = "#0F766E"
TEAL_BRIGHT = "#2DD4BF"
CLEAR = "#0D9488"  # the "Clear" tone: the C and the dot of Clear·MD
CLEAR_BRIGHT = "#99F6E4"
INK = "#1B2733"
WHITE = "#FFFFFF"

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


def _rgba(colour: str) -> tuple[int, int, int, int]:
    value = colour.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), 255


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


def _render(size: int, paint: Callable[[ImageDraw.ImageDraw, float], None]) -> Image.Image:
    big = Image.new("RGBA", (size * SUPERSAMPLE, size * SUPERSAMPLE), (0, 0, 0, 0))
    paint(ImageDraw.Draw(big), big.width)
    return big.resize((size, size), Image.Resampling.LANCZOS)


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


# --- File icons: a page in the format's colour with its initials; a folder ------------------------


@dataclass(frozen=True)
class FileIcon:
    name: str  # the asset's name: what ``presenter.icons.icon_for`` returns
    letters: str
    colour: str  # white letters on it pass 4.5:1


FILE_ICONS = (
    FileIcon("pdf", "PDF", "#C62828"),
    FileIcon("docx", "W", "#2B6CC4"),
    FileIcon("xlsx", "X", "#17803A"),
    FileIcon("pptx", "P", "#C2410C"),
    FileIcon("odt", "O", "#3949AB"),
    FileIcon("tex", "TeX", "#00796B"),
    FileIcon("html", "</>", "#BE185D"),
    FileIcon("csv", "CSV", "#4D7C0F"),
    FileIcon("epub", "E", "#7B3FA0"),
    FileIcon("ipynb", "NB", "#A16207"),
    FileIcon("txt", "T", "#5B6672"),
    FileIcon("markdown", "M↓", "#334155"),
    FileIcon("unknown", "?", "#64748B"),
)
ICON_SIZE = 28  # the list's rows; @2x for high-density screens
FOLDER_BACK, FOLDER_FRONT = "#C98A0B", "#E3A008"
LETTER_SIZES = {1: 13.0, 2: 9.5, 3: 7.2}  # px at 28 px: fewer letters, larger


def _darker(colour: str, amount: float = 0.22) -> tuple[int, int, int, int]:
    r, g, b, a = _rgba(colour)
    return round(r * (1 - amount)), round(g * (1 - amount)), round(b * (1 - amount)), a


def _font(size: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT), round(size))


def file_icon_png(icon: FileIcon, size: int) -> Image.Image:
    def paint(draw: ImageDraw.ImageDraw, px: float) -> None:
        u = px / ICON_SIZE  # pixels per unit of the 28-unit box
        left, top, right, bottom, fold = 3 * u, 0.5 * u, 25 * u, 27.5 * u, 7 * u
        draw.rounded_rectangle((left, top, right, bottom), 2.5 * u, _rgba(icon.colour))
        draw.polygon(  # the folded corner: cut, then drawn darker
            [(right - fold, top), (right + 1, top), (right + 1, top + fold + 1)], fill=(0, 0, 0, 0)
        )
        draw.polygon(
            [(right - fold, top), (right - fold, top + fold), (right, top + fold)],
            fill=_darker(icon.colour),
        )
        letters = icon.letters
        font = _font(LETTER_SIZES[min(len(letters), 3)] * u)
        draw.text((14 * u, 17 * u), letters, fill=_rgba(WHITE), font=font, anchor="mm")

    return _render(size, paint)


def folder_png(size: int) -> Image.Image:
    def paint(draw: ImageDraw.ImageDraw, px: float) -> None:
        u = px / ICON_SIZE
        draw.rounded_rectangle((1 * u, 3 * u, 12 * u, 9 * u), 2 * u, _rgba(FOLDER_BACK))
        draw.rounded_rectangle((1 * u, 6 * u, 27 * u, 25 * u), 3 * u, _rgba(FOLDER_BACK))
        draw.rounded_rectangle((1 * u, 10 * u, 27 * u, 25 * u), 3 * u, _rgba(FOLDER_FRONT))

    return _render(size, paint)


# --- The executable: its icon and the splash shown while it unpacks (feature 006) ---------------

SPLASH = (480, 200)
WORDMARK_FONT_SIZE = 40


def ico_bytes() -> bytes:
    out = io.BytesIO()
    app_png(256).save(out, format="ICO", sizes=[(size, size) for size in APP_SIZES])
    return out.getvalue()


def splash_png() -> Image.Image:
    """The app icon and Clear·MD on the rail's ink, the dot in the "Clear" tone."""
    width, height = SPLASH
    image = Image.new("RGBA", SPLASH, _rgba(INK))
    icon = app_png(96)
    image.alpha_composite(icon, (40, (height - icon.height) // 2))
    draw = ImageDraw.Draw(image)
    font = _font(WORDMARK_FONT_SIZE)
    x: float = 40 + icon.width + 28
    middle = height / 2
    for part, colour in (("Clear", "#F3F5F7"), ("·", CLEAR_BRIGHT), ("MD", "#F3F5F7")):
        draw.text((x, middle), part, fill=_rgba(colour), font=font, anchor="lm")
        x += draw.textlength(part, font=font)
    return image


# --- Everything, as {relative path: bytes} ---------------------------------------------------


def _png_bytes(image: Image.Image) -> bytes:
    out = io.BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue()


def assets() -> dict[str, bytes]:
    """Every asset file, by its path under ``frontend/assets``."""
    files: dict[str, bytes] = {}
    for colours in MARKS:
        files[f"logo/clearmd-{colours.name}.svg"] = mark_svg(colours).encode()
        for size in MARK_SIZES:
            files[f"logo/clearmd-{colours.name}-{size}.png"] = _png_bytes(mark_png(colours, size))
    files["logo/clearmd-app.svg"] = app_svg().encode()
    files["logo/clearmd.ico"] = ico_bytes()
    files["logo/splash.png"] = _png_bytes(splash_png())
    for size in APP_SIZES:
        files[f"logo/clearmd-app-{size}.png"] = _png_bytes(app_png(size))
    for icon in FILE_ICONS:
        files[f"icons/{icon.name}.png"] = _png_bytes(file_icon_png(icon, ICON_SIZE))
        files[f"icons/{icon.name}@2x.png"] = _png_bytes(file_icon_png(icon, 2 * ICON_SIZE))
    files["icons/folder.png"] = _png_bytes(folder_png(ICON_SIZE))
    files["icons/folder@2x.png"] = _png_bytes(folder_png(2 * ICON_SIZE))
    return files


def main() -> int:
    for relative, data in assets().items():
        target = ASSETS / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(target.relative_to(ASSETS.parents[3]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
