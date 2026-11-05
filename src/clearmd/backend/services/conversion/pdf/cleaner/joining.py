"""A block's lines as one text: broken words joined, hyphens kept where they are real."""

import re

from clearmd.backend.services.conversion.pdf.model import SOFT_HYPHEN, Line

SIZE_CHANGE = 0.1  # text this much larger or smaller is another block (a caption, a note)


def joined(parts: list[str]) -> str:
    """The lines of one block as one text; built once, whatever its length."""
    pieces: list[str] = []
    for part in parts:
        if not pieces:
            pieces.append(part)
            continue
        previous = pieces[-1]
        if previous.endswith(SOFT_HYPHEN):
            # A word broken at the end of the line; before a capital it was a real hyphen
            # ("socio-Economic"), which PDFium also gives as a broken word.
            pieces[-1] = previous[:-1] + ("-" if part[:1].isupper() else "")
            pieces.append(part)
        elif previous.endswith("-") and previous[-2:-1].isalnum() and part[:1].isalnum():
            pieces.append(part)  # "2012-" + "2016": the hyphen stays, the two are one again
        else:
            pieces.append(" ")
            pieces.append(part)
    return _SOFT_INSIDE.sub(_unbroken, "".join(pieces)).replace(SOFT_HYPHEN, "")


_SOFT_INSIDE = re.compile(SOFT_HYPHEN + r"(?=(\w))")


def _unbroken(found: re.Match[str]) -> str:
    """A word PDFium joined itself: before a capital it was a real hyphen ("socio-Economic");
    before a small letter, a hyphenation (also "well-known" then reads "wellknown": PDFium
    cannot tell them apart, and the broken word is by far the commoner)."""
    return "-" if found.group(1).isupper() else ""


def is_resized(last: Line, line: Line) -> bool:
    return abs(line.size - last.size) > SIZE_CHANGE * max(last.size, line.size, 1.0)
