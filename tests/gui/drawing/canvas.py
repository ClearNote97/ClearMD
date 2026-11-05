"""Colours, fonts and the supersampled canvas every drawing uses."""

from collections.abc import Callable
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
REGULAR_FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
# The dev container's DejaVu Sans Bold (Debian 12): another version draws the letters differently.
FONT_SHA256 = "0d977336a6d5fba34eab8e3199eb218327161b5143749f802982c2bc34df0c96"
SUPERSAMPLE = 8  # drawn this many times larger, then reduced: smooth edges

TEAL = "#0F766E"
TEAL_BRIGHT = "#2DD4BF"
CLEAR = "#0D9488"  # the "Clear" tone: the C and the dot of Clear·MD
CLEAR_BRIGHT = "#99F6E4"
INK = "#1B2733"
WHITE = "#FFFFFF"


def _rgba(colour: str) -> tuple[int, int, int, int]:
    value = colour.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), 255


def _render(size: int, paint: Callable[[ImageDraw.ImageDraw, float], None]) -> Image.Image:
    big = Image.new("RGBA", (size * SUPERSAMPLE, size * SUPERSAMPLE), (0, 0, 0, 0))
    paint(ImageDraw.Draw(big), big.width)
    return big.resize((size, size), Image.Resampling.LANCZOS)


def _font(size: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT), round(size))
