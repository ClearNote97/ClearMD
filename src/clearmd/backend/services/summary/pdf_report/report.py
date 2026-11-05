"""``PdfReport``: the summary as Resumen_ClearMD.pdf, from the same content as the Markdown."""

from clearmd.backend.schemas.formats import PDF_SUMMARY_NAME
from clearmd.backend.schemas.models import OutputRootReport
from clearmd.backend.services.summary.content import (
    MARKDOWN_FOLDER,
    SummaryBuilder,
    SummaryContent,
)
from clearmd.backend.services.summary.pdf_report.blocks import Blocks
from clearmd.backend.services.summary.pdf_report.canvas import Canvas
from clearmd.backend.services.summary.pdf_report.table import table
from clearmd.backend.services.summary.pdf_report.theme import Run
from clearmd.backend.use_cases.output_files import atomic_write_bytes
from clearmd.i18n import Catalog


class PdfReport:
    def __init__(self, catalog: Catalog, *, version: str) -> None:
        self._catalog = catalog
        self._blocks = Blocks(catalog)
        self._builder = SummaryBuilder(catalog, version=version)

    def write(self, report: OutputRootReport) -> None:
        data = self.render(self._builder.build(report))
        atomic_write_bytes(report.root / PDF_SUMMARY_NAME, data, inside=report.root)

    def render(self, content: SummaryContent) -> bytes:
        blocks = self._blocks
        canvas = Canvas(self._catalog.text("summary.title"))
        canvas.new_page()
        blocks.band(canvas, content)
        blocks.headline(canvas, content)
        text = self._catalog.text
        blocks.heading(canvas, text("summary.where_title"))
        blocks.paragraph(canvas, [Run(text("summary.where", folder=f"{MARKDOWN_FOLDER}/"))])
        if content.attention:
            blocks.heading(canvas, text("summary.attention"))
            for entry in content.attention:
                blocks.entry(canvas, entry)
        if content.converted:
            blocks.heading(canvas, text("summary.converted"))
            table(self._catalog, canvas, content)
        for key, entries in (
            ("summary.left_out", content.left_out),
            ("summary.kept", content.kept),
            ("summary.cancelled", content.cancelled),
        ):
            if entries:
                blocks.heading(canvas, text(key))
                for entry in entries:
                    blocks.entry(canvas, entry)
        return canvas.save()
