"""The page's image objects with their place, forms' included (feature 012)."""

import ctypes
from collections.abc import Iterator

import pypdfium2.raw as raw

from clearmd.backend.services.conversion.pdf.pdfium.document import finite
from clearmd.backend.services.conversion.pdf.pdfium.page_objects import MAX_PAGE_OBJECTS

MIN_PICTURE_POINTS = 24.0  # smaller: a bullet, a rule, a logo's speck
MAX_FORM_DEPTH = 4  # forms inside forms


def image_objects(page: object) -> Iterator[tuple[object, list[float]]]:
    """The page's image objects with their place: (left, bottom, right, top)."""
    left, bottom, right, top = (ctypes.c_float() for _ in range(4))
    visited = 0
    pending: list[tuple[object, int, list[float] | None]] = [(page, 0, None)]
    while pending:
        holder, depth, place = pending.pop(0)
        in_form = holder is not page
        count = (
            raw.FPDFFormObj_CountObjects(holder) if in_form else raw.FPDFPage_CountObjects(holder)
        )
        for index in range(max(count, 0)):
            visited += 1
            if visited > MAX_PAGE_OBJECTS:
                return
            obj = (
                raw.FPDFFormObj_GetObject(holder, index)
                if in_form
                else raw.FPDFPage_GetObject(holder, index)
            )
            if not obj:
                continue
            kind = raw.FPDFPageObj_GetType(obj)
            if kind not in (raw.FPDF_PAGEOBJ_IMAGE, raw.FPDF_PAGEOBJ_FORM):
                continue
            box = place
            if box is None:
                raw.FPDFPageObj_GetBounds(
                    obj, *(ctypes.byref(v) for v in (left, bottom, right, top))
                )
                box = [finite(v.value) for v in (left, bottom, right, top)]
            if kind == raw.FPDF_PAGEOBJ_FORM:
                if depth < MAX_FORM_DEPTH:
                    pending.append((obj, depth + 1, box))
            elif box[2] - box[0] >= MIN_PICTURE_POINTS and box[3] - box[1] >= MIN_PICTURE_POINTS:
                yield obj, box
