"""The file icons: a page in the format's colour with its initials, and a folder."""

from dataclasses import dataclass

from gui.drawing.canvas import WHITE, _font, _render, _rgba
from PIL import Image, ImageDraw

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
