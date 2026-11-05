"""Pillow marks for the window (ADR-0027): the file icons, the logo, the list's checkbox, a row's
number and a heading's cell."""

from functools import cache
from importlib.resources import files

from PIL import Image, ImageDraw, ImageFont

from clearmd.frontend.ttk.visuals.shapes import SUPERSAMPLE, rgba

ASSETS = files("clearmd.frontend") / "assets"


@cache
def icon(name: str, *, double: bool = False) -> Image.Image:
    """A file icon from ``frontend/assets/icons`` (28 px; 56 px with ``double``), read once.
    Shared: callers compose it onto new images, never draw on it."""
    resource = ASSETS / "icons" / (f"{name}@2x.png" if double else f"{name}.png")
    with resource.open("rb") as stream:
        image = Image.open(stream)
        image.load()
    return image


def logo(name: str) -> Image.Image:
    """A logo file from ``frontend/assets/logo`` (``clearmd-mark-dark-40`` and so on)."""
    with (ASSETS / "logo" / f"{name}.png").open("rb") as stream:
        image = Image.open(stream)
        image.load()
    return image


CHECKBOX = 16  # a list row's box (feature 007)
CHECK_ZONE = CHECKBOX + 8  # its width with the space after it


def checkbox(state: str, *, box: str, border: str, mark: str) -> Image.Image:
    """A list's checkbox: ``state`` is "off", "on" or "some" (the header of a partly selected
    list). Checked boxes are filled with ``box`` and carry a ``mark``."""
    s = SUPERSAMPLE * 2
    size = CHECKBOX * s
    big = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(big)
    radius = 3 * s
    if state == "off":
        draw.rounded_rectangle((0, 0, size - 1, size - 1), radius, fill=rgba(border))
        draw.rounded_rectangle((2 * s, 2 * s, size - 1 - 2 * s, size - 1 - 2 * s), radius - s,
                               fill=(0, 0, 0, 0))  # fmt: skip
    else:
        draw.rounded_rectangle((0, 0, size - 1, size - 1), radius, fill=rgba(box))
        width = round(2.2 * s)
        if state == "on":
            points = [(3.5 * s, 8.2 * s), (6.6 * s, 11.2 * s), (12.5 * s, 4.8 * s)]
            draw.line(points, fill=rgba(mark), width=width, joint="curve")
        else:
            draw.line([(4 * s, 8 * s), (12 * s, 8 * s)], fill=rgba(mark), width=width)
    return big.resize((CHECKBOX, CHECKBOX), Image.Resampling.LANCZOS)


def numbered(
    number: int,
    file_icon: Image.Image,
    colour: str,
    *,
    digits: int,
    check: Image.Image | None = None,
) -> Image.Image:
    """A list row's picture: its checkbox, the row's number right-aligned, then its file icon
    (ADR-0027, feature 007)."""
    font = ImageFont.load_default(size=14)
    box = CHECK_ZONE if check is not None else 0
    number_width = 12 + 9 * max(digits, 2)
    width = box + number_width + file_icon.width
    row = Image.new("RGBA", (width, file_icon.height), (0, 0, 0, 0))
    if check is not None:
        row.alpha_composite(check, (0, (row.height - check.height) // 2))
    draw = ImageDraw.Draw(row)
    draw.text(
        (box + number_width - 12, row.height / 2), str(number), fill=rgba(colour), font=font,
        anchor="rm",
    )  # fmt: skip
    row.alpha_composite(file_icon, (box + number_width, 0))
    return row


def heading_cell(height: int, ground: str, line: str) -> Image.Image:
    """A list heading's background: ``ground`` with a faint line at its right edge, where a column
    can be resized (feature 007)."""
    cell = Image.new("RGBA", (24, height), rgba(ground))
    draw = ImageDraw.Draw(cell)
    draw.line((23, height // 4, 23, height - height // 4), fill=rgba(line), width=1)
    return cell
