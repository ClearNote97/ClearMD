"""A number per font of the document, and each page's characters by font (feature 008)."""

import ctypes
from collections import Counter
from collections.abc import Iterator

import pypdfium2.raw as raw

_BOLD_NAMES = ("bold", "black", "heavy", "semibold", "demi")
_FORCE_BOLD = 1 << 18  # the font descriptor's ForceBold flag
MAX_PAGE_CHARS = 200_000  # a dense page of a book holds ~5,000; past this, the rest is left out


class Fonts:
    """A number per font of the document: PDFium keeps each font once per open document, so its
    address (with its name and flags) names it in both passes, and two fonts that share a name
    stay two (adversarial check of 008). Its codes; how many PDFium could not map; its weight."""

    def __init__(self) -> None:
        self.number: dict[tuple[int, bytes, int], int] = {}
        self.codes: list[Counter[int]] = []
        self.errors: list[int] = []  # characters PDFium found no map for
        self.bold: list[bool] = []

    def at(self, textpage: object, index: int, address: int) -> int:
        name = ctypes.create_string_buffer(128)
        flags = ctypes.c_int()
        raw.FPDFText_GetFontInfo(textpage, index, name, len(name), ctypes.byref(flags))
        key = (address, name.value, flags.value)
        if key not in self.number:
            self.number[key] = len(self.codes)
            self.codes.append(Counter())
            self.errors.append(0)
            # By its name ("Helvetica-Bold", "Arial,Bold") or the ForceBold flag only: a font
            # that declares no weight gets one from its stems, and plain Arial reads 695.
            lowered = name.value.decode("latin-1").lower()
            self.bold.append(
                bool(flags.value & _FORCE_BOLD) or any(word in lowered for word in _BOLD_NAMES)
            )
        return self.number[key]

    def unmapped(self, font: int) -> bool:
        """Most of its characters had no map (one mapped space first proves nothing)."""
        return self.errors[font] * 2 >= max(sum(self.codes[font].values()), 1)


def each_font(textpage: object, fonts: Fonts) -> Iterator[tuple[int, int]]:
    """(index, font) of every character of the page; the font is looked up once per text
    object, not per character."""
    last_object: int | None = None
    font = 0
    for index in range(min(max(raw.FPDFText_CountChars(textpage), 0), MAX_PAGE_CHARS)):
        handle = raw.FPDFText_GetTextObject(textpage, index)
        address = ctypes.cast(handle, ctypes.c_void_p).value or 0
        if address != last_object:
            last_object = address
            pointer = raw.FPDFTextObj_GetFont(handle) if handle else None
            font_address = (ctypes.cast(pointer, ctypes.c_void_p).value or 0) if pointer else 0
            font = fonts.at(textpage, index, font_address)
        yield index, font


def count(textpage: object, fonts: Fonts) -> None:
    """The first pass: each font's codes."""
    for index, font in each_font(textpage, fonts):
        fonts.codes[font][raw.FPDFText_GetUnicode(textpage, index)] += 1
        if raw.FPDFText_HasUnicodeMapError(textpage, index) == 1:
            fonts.errors[font] += 1
