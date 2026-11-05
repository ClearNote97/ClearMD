"""The blocks of the summary page: the band, the headline, headings, paragraphs and entries."""

from clearmd.backend.schemas.notes import ConversionNote
from clearmd.backend.services.summary.content import Entry, SummaryContent
from clearmd.backend.services.summary.pdf_report import metrics
from clearmd.backend.services.summary.pdf_report.canvas import Canvas
from clearmd.backend.services.summary.pdf_report.text import displayed, latin, wrap
from clearmd.backend.services.summary.pdf_report.theme import (
    ACCENT,
    BAND,
    BORDER,
    HEADING_ROOM,
    HEIGHT,
    LEFT_OUT,
    MARGIN,
    MARK_COLOURS,
    MAX_DETAIL,
    MUTED,
    NOTE_ITEMS,
    SHAPE,
    WHITE,
    WIDTH,
    Run,
)
from clearmd.i18n import Catalog


class Blocks:
    """Draws the pieces of the page on a ``Canvas``, in the words of one catalog."""

    def __init__(self, catalog: Catalog) -> None:
        self._catalog = catalog

    def band(self, canvas: Canvas, content: SummaryContent) -> None:
        canvas.rect(0, HEIGHT - BAND, WIDTH, BAND, ACCENT)
        title = self._catalog.text("summary.title")
        canvas.text(MARGIN, HEIGHT - 44, latin(title), 20, Run(title, True, WHITE))
        line = latin(content.batch_line)
        canvas.text(MARGIN, HEIGHT - 62, line, 9, Run(line, False, SHAPE))
        canvas.y = HEIGHT - BAND - 28

    def headline(self, canvas: Canvas, content: SummaryContent) -> None:
        runs = [Run(content.headline, True)]
        if content.attention_line:
            runs.append(Run(" " + content.attention_line, False, MUTED))
        lines = list(wrap(runs, 14, WIDTH - 2 * MARGIN - 24))
        canvas.room(20 * len(lines))
        canvas.circle(MARGIN + 7, canvas.y + 4, 7, MARK_COLOURS[content.mark])
        for line in lines:
            self.line(canvas, MARGIN + 24, line, 14)
            canvas.y -= 20
        canvas.y -= 6

    def heading(self, canvas: Canvas, text: str) -> None:
        canvas.room(HEADING_ROOM)
        canvas.y -= 16
        canvas.text(MARGIN, canvas.y, latin(text), 12, Run(text, True, ACCENT))
        canvas.rect(MARGIN, canvas.y - 6, WIDTH - 2 * MARGIN, 0.8, BORDER)
        canvas.y -= 22

    def paragraph(
        self, canvas: Canvas, runs: list[Run], *, indent: float = 0, size: float = 10
    ) -> None:
        for line in wrap(runs, size, WIDTH - 2 * MARGIN - indent):
            canvas.room(size + 4)
            self.line(canvas, MARGIN + indent, line, size)
            canvas.y -= size + 4

    def line(self, canvas: Canvas, x: float, runs: list[Run], size: float) -> None:
        """Words of one style together, one text object: the font spaces them itself."""
        merged: list[Run] = []
        for run in runs:
            if merged and (merged[-1].bold, merged[-1].colour) == (run.bold, run.colour):
                merged[-1] = Run(merged[-1].text + run.text, run.bold, run.colour)
            else:
                merged.append(run)
        for run in merged:
            canvas.text(x, canvas.y, run.text, size, run)
            x += metrics.width(run.text, size, run.bold)

    def entry(self, canvas: Canvas, entry: Entry) -> None:
        canvas.room(18)
        colour = MARK_COLOURS[entry.mark] if entry.mark else LEFT_OUT
        canvas.circle(MARGIN + 4, canvas.y + 3.5, 3.5, colour)
        runs = [Run(displayed(entry.name), True)]
        if entry.folder:
            folder = self._catalog.text("summary.in_folder", folder=displayed(entry.folder))
            runs.append(Run(" " + folder, False, MUTED))
        if entry.result:
            runs.append(Run(f" » {displayed(entry.result)}", False, MUTED))  # no "→" in Latin
        if entry.message:
            runs.append(Run(f" — {entry.message}"))
        self.paragraph(canvas, runs, indent=14)
        for note in entry.notes:
            self.paragraph(canvas, [Run(f"· {self.describe(note)}")], indent=26, size=9)
        if entry.detail:
            shown = displayed(entry.detail, MAX_DETAIL)
            detail = f"{self._catalog.text('summary.technical_detail')}: {shown}"
            self.paragraph(canvas, [Run(detail, False, MUTED)], indent=26, size=8)
        canvas.y -= 4

    def describe(self, note: ConversionNote) -> str:
        shown = []
        for item in note.items[:NOTE_ITEMS]:
            subject = displayed(item.subject)
            reason = item.reason and self._catalog.text(f"note.reason.{item.reason}")
            shown.append(f"{subject} ({reason})" if reason else subject)
        listed = ", ".join(shown)
        if len(note.items) > NOTE_ITEMS:
            listed += self._catalog.text("note.and_more", count=len(note.items) - NOTE_ITEMS)
        return self._catalog.text(note.kind.key, items=listed)
