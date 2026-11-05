"""The page's thin paths: ruled-table rules and fraction bars (feature 013, 015)."""

import ctypes

import pypdfium2.raw as raw

from clearmd.backend.services.conversion.pdf.latex import Bar
from clearmd.backend.services.conversion.pdf.lattice import Rule, rule
from clearmd.backend.services.conversion.pdf.pdfium.document import finite

BAR_THICKNESS = 1.5  # points: a fraction's bar is a thin line
MIN_BAR = 2.0  # points: shorter is a dot
MAX_BAR = 400.0  # points: longer is a rule across the page
MAX_BARS = 2000  # a page's bars looked at
MAX_PAGE_OBJECTS = 100_000  # a page's objects looked at for pictures, forms' included


def page_rules(page: object) -> tuple[list[Rule], list[Bar]]:
    """The page's thin paths: the rules a ruled table is drawn with (013), and the short level
    ones an equation draws (its fractions' bars, 015)."""
    found: list[Rule] = []
    bars: list[Bar] = []
    left, bottom, right, top = (ctypes.c_float() for _ in range(4))
    for index in range(min(max(raw.FPDFPage_CountObjects(page), 0), MAX_PAGE_OBJECTS)):
        obj = raw.FPDFPage_GetObject(page, index)
        if not obj or raw.FPDFPageObj_GetType(obj) != raw.FPDF_PAGEOBJ_PATH:
            continue
        raw.FPDFPageObj_GetBounds(obj, *(ctypes.byref(v) for v in (left, bottom, right, top)))
        box = [finite(v.value) for v in (left, bottom, right, top)]
        found_rule = rule(*box)
        if found_rule is not None:
            found.append(found_rule)
        if box[3] - box[1] <= BAR_THICKNESS and MIN_BAR <= box[2] - box[0] <= MAX_BAR:
            bars.append(Bar(box[0], box[2], (box[1] + box[3]) / 2))
    return found, bars[:MAX_BARS]
