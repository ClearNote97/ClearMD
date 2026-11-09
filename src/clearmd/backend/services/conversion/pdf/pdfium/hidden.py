"""Text a reader of the page cannot see (ADR-0054): left out of the Markdown, and said.

An AI reads every character a PDF holds; a person reads only what the page shows. Text placed
off the page, drawn too small to read, or drawn invisible on a page with no picture under it can
carry instructions no one sees. Such characters become spaces (their place is kept, so the
reader's indices into PDFium's text page still match) and are counted.

Never hidden: the invisible text a scanner's text recognition lays over the page's picture (the
only text a scanned PDF has), and white text, which may sit on a coloured box: ClearMD cannot
see the background, so it does not guess.
"""

import pypdfium2.raw as raw

from clearmd.backend.services.conversion.pdf.model import Chars

OFF_PAGE = 72.0  # points (an inch) past the edge: text that far out was never meant to be seen;
# nearer, it may be a line the page cuts at its edge, which a reader half sees
MIN_FONT_SIZE = 1.0  # points: smaller than anyone can read
MAX_PAGE_OBJECTS = 100_000  # a page's objects looked at (as for its rules and pictures)
SPACE = 0x20


def _invisible_without_picture(page: object) -> bool:
    """Whether the page draws invisible text and has no picture for it to lie on."""
    invisible = picture = False
    for index in range(min(max(raw.FPDFPage_CountObjects(page), 0), MAX_PAGE_OBJECTS)):
        obj = raw.FPDFPage_GetObject(page, index)
        if not obj:
            continue
        kind = raw.FPDFPageObj_GetType(obj)
        if kind == raw.FPDF_PAGEOBJ_IMAGE:
            picture = True
        elif kind == raw.FPDF_PAGEOBJ_TEXT and (
            raw.FPDFTextObj_GetTextRenderMode(obj) == raw.FPDF_TEXTRENDERMODE_INVISIBLE
        ):
            invisible = True
    return invisible and not picture


def hide_unseen(chars: Chars, textpage: object, page: object, width: float, height: float) -> int:
    """Turn the page's unseen characters into spaces; how many (not counting spaces) there were."""
    invisible = _invisible_without_picture(page)
    hidden = 0
    for index, code in enumerate(chars.codes):
        if code <= SPACE:
            continue
        off_page = (
            chars.rights[index] < -OFF_PAGE
            or chars.lefts[index] > width + OFF_PAGE
            or chars.tops[index] < -OFF_PAGE
            or chars.bottoms[index] > height + OFF_PAGE
        )
        tiny = 0 < chars.font_sizes[index] < MIN_FONT_SIZE
        unseen = off_page or tiny
        if not unseen and invisible:
            obj = raw.FPDFText_GetTextObject(textpage, index)
            unseen = bool(obj) and (
                raw.FPDFTextObj_GetTextRenderMode(obj) == raw.FPDF_TEXTRENDERMODE_INVISIBLE
            )
        if unseen:
            chars.codes[index] = SPACE
            hidden += 1
    return hidden
