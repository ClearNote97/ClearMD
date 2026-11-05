"""The cleaner's entry: running lines out, footnotes held, blocks written (008, ADR-0030)."""

from dataclasses import dataclass, field

from clearmd.backend.services.conversion.markdown_out import neutralize, tidy
from clearmd.backend.services.conversion.pdf.cleaner.footnotes import split_footnotes
from clearmd.backend.services.conversion.pdf.cleaner.running import without_running
from clearmd.backend.services.conversion.pdf.cleaner.sizes import body_size, levels
from clearmd.backend.services.conversion.pdf.cleaner.writer import Writer
from clearmd.backend.services.conversion.pdf.model import Document


@dataclass
class Cleaned:
    markdown: str
    running_removed: int = 0  # header, footer and page-number lines left out
    headings: int = 0
    empty_pages: list[int] = field(default_factory=list)  # 1-based: no text (scanned?)


def clean(document: Document) -> Cleaned:
    pages = [page.lines for page in document.pages]
    body = body_size(pages)
    heights = [page.height for page in document.pages]
    pages, removed = without_running(pages, heights, body)
    body = body_size(pages) or body
    writer = Writer(body, levels(pages, body))
    # A page with only a header or a number left (a scan with a printed folio) has no text.
    empty = [number for number, lines in enumerate(pages, start=1) if not lines]
    for lines in pages:
        text, notes = split_footnotes(lines, body)
        writer.set_typical(text)
        for line in text:
            writer.add(line)
        writer.page_break()
        if notes:
            writer.hold(notes)
    markdown = tidy(neutralize(writer.finish()))
    return Cleaned(markdown, removed, writer.buffer.headings, empty)
