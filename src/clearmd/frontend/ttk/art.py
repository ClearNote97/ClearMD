"""Pillow drawings for the window (ADR-0027): rounded shapes, the background shape, the list's rows.

Everything is drawn larger and reduced, so edges are smooth; the results become Tk images in
``brand`` and the components.
"""

from functools import cache
from importlib.resources import files

from PIL import Image, ImageDraw, ImageFont

from clearmd.frontend.design.metrics import SPACE

SUPERSAMPLE = 4
ASSETS = files("clearmd.frontend") / "assets"

RGBA = tuple[int, int, int, int]


def rgba(colour: str, alpha: int = 255) -> RGBA:
    value = colour.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), alpha


def rounded(
    width: int,
    height: int,
    radius: int,
    fill: str,
    *,
    border: str | None = None,
    ring: str | None = None,
    dashed: bool = False,
    ground: str | None = None,
) -> Image.Image:
    """A rounded rectangle; ``ring`` adds a 2 px focus ring around it. Its corners show ``ground``
    (transparent without it): a ttk element paints no background of its own."""
    s = SUPERSAMPLE
    big = Image.new("RGBA", (width * s, height * s), rgba(ground) if ground else (0, 0, 0, 0))
    draw = ImageDraw.Draw(big)
    inset = 3 * s if ring else 0  # room for the ring
    box = (inset, inset, width * s - 1 - inset, height * s - 1 - inset)
    if ring:
        draw.rounded_rectangle(
            (0, 0, width * s - 1, height * s - 1), radius * s + inset, fill=rgba(ring)
        )
        draw.rounded_rectangle(
            (s, s, width * s - 1 - s, height * s - 1 - s),
            radius * s + inset - s,
            fill=rgba(ground) if ground else (0, 0, 0, 0),
        )
    if border and not dashed:
        draw.rounded_rectangle(box, radius * s, fill=rgba(border))
        box = (box[0] + s, box[1] + s, box[2] - s, box[3] - s)
        draw.rounded_rectangle(box, radius * s - s, fill=rgba(fill))
    else:
        draw.rounded_rectangle(box, radius * s, fill=rgba(fill))
    if border and dashed:
        _dashes(draw, box, radius * s, border, 2 * s)
    return big.resize((width, height), Image.Resampling.LANCZOS)


def _dashes(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    radius: int,
    colour: str,
    width: int,
) -> None:
    """A dashed rounded outline: straight dashes on the sides, solid quarter arcs at the corners."""
    left, top, right, bottom = box
    dash, gap = 8 * width // 2, 6 * width // 2
    fill = rgba(colour)
    for x0, y0, x1, y1 in (
        (left + radius, top, right - radius, top),
        (left + radius, bottom, right - radius, bottom),
        (left, top + radius, left, bottom - radius),
        (right, top + radius, right, bottom - radius),
    ):
        length = max(x1 - x0, y1 - y0)
        position = 0
        while position < length:
            end = min(position + dash, length)
            if x0 == x1:
                draw.line((x0, y0 + position, x1, y0 + end), fill=fill, width=width)
            else:
                draw.line((x0 + position, y0, x0 + end, y1), fill=fill, width=width)
            position = end + gap
    diameter = 2 * radius
    for corner, start in (
        ((left, top), 180),
        ((right - diameter, top), 270),
        ((right - diameter, bottom - diameter), 0),
        ((left, bottom - diameter), 90),
    ):
        x, y = corner
        draw.arc((x, y, x + diameter, y + diameter), start, start + 90, fill=fill, width=width)


def surface(
    width: int,
    height: int,
    ground: str,
    shape: str,
    *,
    band: int,
) -> Image.Image:
    """The working area's ground: a soft organic shape in the top right corner, whole within the
    header ``band`` (never cut by the page below it, feature 011)."""
    s = 2  # a large, soft shape: little supersampling needed
    big = Image.new("RGBA", (width * s, height * s), rgba(ground))
    draw = ImageDraw.Draw(big)
    w = width * s
    blob = rgba(shape)
    bottom = max(band - SPACE, 40) * s
    draw.ellipse((w - 300 * s, bottom - 330 * s, w + 140 * s, bottom), fill=blob)
    draw.ellipse((w - 420 * s, bottom - 270 * s, w - 120 * s, bottom - 50 * s), fill=blob)
    return big.resize((width, height), Image.Resampling.LANCZOS)


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


def circle(diameter: int, *, outline: str, fill: str, width: float = 1.5) -> Image.Image:
    """A smooth circle (Tk's own ovals are jagged): ``outline`` around ``fill``."""
    s = SUPERSAMPLE * 2
    big = Image.new("RGBA", (diameter * s, diameter * s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(big)
    draw.ellipse((0, 0, diameter * s - 1, diameter * s - 1), fill=rgba(outline))
    inset = round(width * s)
    draw.ellipse(
        (inset, inset, diameter * s - 1 - inset, diameter * s - 1 - inset), fill=rgba(fill)
    )
    return big.resize((diameter, diameter), Image.Resampling.LANCZOS)
