"""One page's characters, compact, read from PDFium's text page (feature 008, 014).

The hot loop of the reader: its local aliases are kept as they were, they save a lookup per
character.
"""

import ctypes
import math

import pypdfium2.raw as raw

from clearmd.backend.services.conversion.pdf.model import (
    ASLANT,
    CLOCKWISE,
    COUNTERCLOCKWISE,
    UPRIGHT,
    Boxes,
    Chars,
)
from clearmd.backend.services.conversion.pdf.pdfium.document import finite
from clearmd.backend.services.conversion.pdf.pdfium.fonts import Fonts, each_font

TURN_RADIANS = 0.01  # a character turned less than this from a quarter turn is on it


def page_chars(textpage: object, fonts: Fonts) -> Chars:
    """The second pass, one page at a time: its characters, compact."""
    chars = Chars()
    rect = raw.FS_RECTF()
    box, unicode, angle = (
        raw.FPDFText_GetLooseCharBox,
        raw.FPDFText_GetUnicode,
        raw.FPDFText_GetCharAngle,
    )
    pointer = ctypes.byref(rect)
    font_size, origin, placed = (
        raw.FPDFText_GetFontSize,
        raw.FPDFText_GetCharOrigin,
        raw.FPDFText_GetMatrix,
    )
    matrix = raw.FS_MATRIX()
    matrix_pointer = ctypes.byref(matrix)
    x, y = ctypes.c_double(), ctypes.c_double()
    origin_x, origin_y = ctypes.byref(x), ctypes.byref(y)
    # The same font with the same box height is the same size, its baseline the same height above
    # its box: PDFium is asked again only when either changes (review of 014: the two calls per
    # character cost a quarter of the reading).
    measured: tuple[int, float, float, float] | None = None  # font, height, size, baseline lift
    for index, font in each_font(textpage, fonts):
        box(textpage, index, pointer)
        bottom, top = finite(rect.bottom), finite(rect.top)
        code = unicode(textpage, index)
        chars.codes.append(min(code, 0x10FFFF + 1))  # past Unicode: unreadable
        chars.fonts.append(font)
        chars.sizes.append(max(top - bottom, 0.0))
        chars.bottoms.append(bottom)
        chars.tops.append(top)
        chars.lefts.append(finite(rect.left))
        chars.rights.append(finite(rect.right))
        turned = angle(textpage, index)
        upright = turned == 0.0
        chars.turns.append(UPRIGHT if upright else _turn(turned))  # nearly all: upright
        height = top - bottom
        if upright and measured is not None and measured[:2] == (font, height):
            chars.font_sizes.append(measured[2])
            chars.baselines.append(bottom + measured[3])
        else:
            # The size as drawn: the font's size scaled by its matrix ("1 Tf" and a 9.46 matrix);
            # its height, the matrix's y column ("50 Tz" or "3 0 0 1 cm" scale the width alone).
            scale = (
                math.hypot(matrix.c, matrix.d) if placed(textpage, index, matrix_pointer) else 1.0
            )
            size = finite(font_size(textpage, index) * scale)
            baseline = finite(y.value) if origin(textpage, index, origin_x, origin_y) else bottom
            chars.font_sizes.append(size)
            chars.baselines.append(baseline)
            if upright and code > 0x20:
                measured = (font, height, size, baseline - bottom)
        chars.bold.append(fonts.bold[font])
    return chars


def _turn(angle: float) -> int:
    """How a character is turned, from PDFium's angle (radians, 0 to 2π, measured clockwise: a
    table set sideways to read upwards is at 3π/2)."""
    for target, turn in ((0, UPRIGHT), (2 * math.pi, UPRIGHT), (0.5 * math.pi, CLOCKWISE)):
        if abs(angle - target) < TURN_RADIANS:
            return turn
    return COUNTERCLOCKWISE if abs(angle - 1.5 * math.pi) < TURN_RADIANS else ASLANT


def tight_boxes(textpage: object) -> Boxes:
    rect = [ctypes.c_double() for _ in range(4)]
    pointers = [ctypes.byref(value) for value in rect]

    def box(index: int) -> tuple[float, float, float, float] | None:
        if not raw.FPDFText_GetCharBox(textpage, index, *pointers):
            return None
        left, right, bottom, top = (finite(value.value) for value in rect)
        return (left, right, bottom, top) if right > left and top > bottom else None

    return box
