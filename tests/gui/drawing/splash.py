"""The executable: its icon and the splash shown while it unpacks (feature 006)."""

import io

from gui.drawing.canvas import CLEAR_BRIGHT, INK, REGULAR_FONT, _font, _rgba
from gui.drawing.mark import APP_SIZES, app_png
from PIL import Image, ImageDraw, ImageFont

# --- The executable: its icon and the splash shown while it unpacks (feature 006) ---------------

SPLASH = (520, 240)
WORDMARK_FONT_SIZE = 40
SUBTITLE = "Turn your documents into Markdown"
SUBTITLE_FONT_SIZE = 16
SPLASH_TEXT_POSITION = (40, 214)  # where PyInstaller writes "Loading… N %" (packaging/clearmd.spec)


def ico_bytes() -> bytes:
    out = io.BytesIO()
    app_png(256).save(out, format="ICO", sizes=[(size, size) for size in APP_SIZES])
    return out.getvalue()


def splash_png() -> Image.Image:
    """The app icon, Clear·MD (the dot in the "Clear" tone) and what it does, on the rail's ink;
    the bottom left is left free for the start-up progress (feature 007)."""
    image = Image.new("RGBA", SPLASH, _rgba(INK))
    icon = app_png(96)
    top = 56
    image.alpha_composite(icon, (40, top))
    draw = ImageDraw.Draw(image)
    font = _font(WORDMARK_FONT_SIZE)
    left: float = 40 + icon.width + 28
    x = left
    middle = top + icon.height / 2 - 12
    for part, colour in (("Clear", "#F3F5F7"), ("·", CLEAR_BRIGHT), ("MD", "#F3F5F7")):
        draw.text((x, middle), part, fill=_rgba(colour), font=font, anchor="lm")
        x += draw.textlength(part, font=font)
    subtitle = ImageFont.truetype(str(REGULAR_FONT), SUBTITLE_FONT_SIZE)
    draw.text((left, middle + 34), SUBTITLE, fill=_rgba("#A9B4BE"), font=subtitle, anchor="lm")
    return image
