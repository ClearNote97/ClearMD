"""An Excel workbook cut by whole sheets (feature 027, ADR-0047).

Each part is the workbook itself with only its sheets: formats, widths, merged cells and
formulas stay as they were. A formula that points at a sheet now in another part loses its
target; the ADR says so.
"""

import io
from pathlib import Path

import openpyxl

from clearmd.backend.services.split.text_cut import balanced_cuts


def _sheets(path: Path) -> list[tuple[str, int]]:
    """Each sheet's name and its number of rows, read without loading the cells."""
    workbook = openpyxl.load_workbook(path, read_only=True)
    try:
        return [(sheet.title, max(1, sheet.max_row or 1)) for sheet in workbook.worksheets]
    finally:
        workbook.close()


def cut_xlsx(path: Path, count: int) -> tuple[bytes, ...]:
    """Into ``count`` parts of whole sheets, in order, as even as possible by rows; fewer sheets
    than parts give one part per sheet."""
    sheets = _sheets(path)
    if len(sheets) < 2:
        return (path.read_bytes(),)
    bounds = [0, *balanced_cuts([rows for _, rows in sheets], count), len(sheets)]
    parts = []
    for start, end in zip(bounds, bounds[1:], strict=False):
        keep = {name for name, _ in sheets[start:end]}
        workbook = openpyxl.load_workbook(path)
        try:
            for sheet in list(workbook.worksheets):
                if sheet.title not in keep:
                    workbook.remove(sheet)
            workbook.active = 0
            stream = io.BytesIO()
            workbook.save(stream)
            parts.append(stream.getvalue())
        finally:
            workbook.close()
    return tuple(parts)
