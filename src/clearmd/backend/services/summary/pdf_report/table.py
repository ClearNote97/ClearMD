"""The converted files as a table: a header that repeats on every page, one row per file."""

from clearmd.backend.services.summary.model import SummaryContent
from clearmd.backend.services.summary.pdf_report.canvas import Canvas
from clearmd.backend.services.summary.pdf_report.text import displayed, fit, latin
from clearmd.backend.services.summary.pdf_report.theme import (
    BORDER,
    CELL_SIZE,
    MARGIN,
    SHAPE,
    TABLE_SHARES,
    WIDTH,
    Colour,
    Run,
)
from clearmd.i18n import Catalog


def table(catalog: Catalog, canvas: Canvas, content: SummaryContent) -> None:
    """Draw the converted files (``catalog`` for the column names)."""
    text = catalog.text
    full = WIDTH - 2 * MARGIN
    widths = [share * full for share in TABLE_SHARES]
    header = [
        text("summary.col_document"),
        text("summary.col_folder"),
        text("summary.col_result"),
        text("summary.col_format"),
        text("summary.col_time"),
    ]

    def row(cells: list[str], *, bold: bool, ground: Colour | None) -> None:
        x = MARGIN
        if ground is not None:
            canvas.rect(MARGIN, canvas.y - 5, full, 17, ground)
        for cell, width in zip(cells, widths, strict=True):
            shown = fit(latin(cell), CELL_SIZE, width - 8, bold)
            canvas.text(x + 4, canvas.y, shown, CELL_SIZE, Run(shown, bold))
            x += width
        canvas.y -= 17

    canvas.room(17 + 18)  # the header and a first row together, never the header alone
    pages = canvas.pages
    row(header, bold=True, ground=SHAPE)
    for converted in content.converted:
        canvas.room(18)
        if canvas.pages != pages:  # a new page: the header again
            pages = canvas.pages
            row(header, bold=True, ground=SHAPE)
        cells = [
            displayed(converted.name),
            displayed(converted.folder) or "—",
            displayed(converted.result),
            converted.format,
            converted.time,
        ]
        row(cells, bold=False, ground=None)
        canvas.rect(MARGIN, canvas.y + 12, full, 0.5, BORDER)
