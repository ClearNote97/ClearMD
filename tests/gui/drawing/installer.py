"""The Windows installer's pictures (packaging/installer/images): the tall one beside the Welcome
and Finished pages, and the small mark in the top corner of the other pages. One geometry, drawn
for light and dark Windows, at the sizes Inno Setup 6.7 asks for at 100, 125, 150 and 200 % DPI."""

from gui.drawing.canvas import CLEAR_BRIGHT, SUPERSAMPLE, TEAL_BRIGHT, _font, _rgba
from gui.drawing.mark import MARKS, app_png, mark_png
from PIL import Image, ImageDraw

# Inno Setup keeps the tall picture at 164:314; these are its areas at 100/125/150/200 % DPI.
WIZARD_SIZES = ((202, 386), (269, 515), (336, 643), (430, 824))
SMALL_SIZES = (58, 77, 97, 124)
# The rail's ink, the same as the apps' side rail, in each theme (frontend/design/palette.py).
GROUNDS = {"light": "#1B2733", "dark": "#0F161C"}
CHIP_FILL = "#26333F"  # the rail's hover tone: a chip sits on the rail
CHIP_TEXT = "#A9B4BE"
WORD = "#F3F5F7"
FORMATS = (("PDF", "DOCX", "PPTX"), ("XLSX", "HTML", "EPUB"))


def _chip(
    draw: ImageDraw.ImageDraw, centre: float, top: float, text: str, unit: float, *, accent: bool
) -> None:
    font = _font(11 * unit)
    width = draw.textlength(text, font=font) + 14 * unit
    height = 22 * unit
    box = (centre - width / 2, top, centre + width / 2, top + height)
    fill, ink = (TEAL_BRIGHT, "#0B1F1C") if accent else (CHIP_FILL, CHIP_TEXT)
    draw.rounded_rectangle(box, height / 2, _rgba(fill))
    draw.text((centre, top + height / 2), text, fill=_rgba(ink), font=font, anchor="mm")


def _row(
    draw: ImageDraw.ImageDraw, width: float, top: float, words: tuple[str, ...], unit: float
) -> None:
    font = _font(11 * unit)
    gap = 6 * unit
    widths = [draw.textlength(word, font=font) + 14 * unit for word in words]
    x = (width - sum(widths) - gap * (len(words) - 1)) / 2
    for word, chip in zip(words, widths, strict=True):
        _chip(draw, x + chip / 2, top, word, unit, accent=False)
        x += chip + gap


def wizard_png(size: tuple[int, int], theme: str) -> Image.Image:
    """The app icon, Clear·MD, and the formats flowing down into Markdown, on the rail's ink;
    a large faint mark fills the bottom. No words: the same picture serves every language."""
    # The mark and the icon are drawn at the picture's own size (they smooth their edges
    # themselves); the letters, chips and arrow are drawn larger on a layer, then reduced.
    small = size[0] / 202
    image = Image.new("RGBA", size, _rgba(GROUNDS[theme]))
    ghost = mark_png(MARKS[1], round(240 * small))
    ghost.putalpha(ghost.getchannel("A").point(lambda alpha: alpha * 7 // 100))
    image.alpha_composite(ghost, (round(size[0] - 180 * small), round(size[1] - 150 * small)))
    width, height = size[0] * SUPERSAMPLE, size[1] * SUPERSAMPLE
    unit = width / 202
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font = _font(28 * unit)
    parts = (("Clear", WORD), ("·", CLEAR_BRIGHT), ("MD", WORD))
    x = (width - sum(draw.textlength(part, font=font) for part, _ in parts)) / 2
    for part, colour in parts:
        draw.text((x, 172 * unit), part, fill=_rgba(colour), font=font, anchor="lm")
        x += draw.textlength(part, font=font)
    _row(draw, width, 214 * unit, FORMATS[0], unit)
    _row(draw, width, 242 * unit, FORMATS[1], unit)
    middle = width / 2
    arrow = [(middle, 274 * unit), (middle, 300 * unit)]
    draw.line(arrow, fill=_rgba(TEAL_BRIGHT), width=round(3 * unit))
    head = [(middle - 7 * unit, 293 * unit), (middle, 301 * unit), (middle + 7 * unit, 293 * unit)]
    draw.line(head, fill=_rgba(TEAL_BRIGHT), width=round(3 * unit), joint="curve")
    _chip(draw, middle, 310 * unit, ".md", unit, accent=True)
    image.alpha_composite(layer.resize(size, Image.Resampling.LANCZOS))
    icon = app_png(round(84 * small))
    image.alpha_composite(icon, (round((size[0] - icon.width) / 2), round(52 * small)))
    return image


def small_png(size: int, theme: str) -> Image.Image:
    """The mark alone, transparent: teal on a light header, the bright tones on a dark one."""
    return mark_png(MARKS[0] if theme == "light" else MARKS[1], size)


def installer_images() -> dict[str, Image.Image]:
    """Every picture, by its file name in packaging/installer/images."""
    images: dict[str, Image.Image] = {}
    for theme in GROUNDS:
        suffix = "" if theme == "light" else "-dark"
        for size in WIZARD_SIZES:
            images[f"wizard{suffix}-{size[0]}.png"] = wizard_png(size, theme)
        for side in SMALL_SIZES:
            images[f"small{suffix}-{side}.png"] = small_png(side, theme)
    return images
