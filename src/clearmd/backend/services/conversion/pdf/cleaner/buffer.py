"""The blocks written so far, and the paragraph being built that becomes the next one (008)."""

from clearmd.backend.services.conversion.markdown_out import (
    MARK,
    escape_text,
    heading_text,
    neutralize,
)
from clearmd.backend.services.conversion.pdf.cleaner.flow import Flow
from clearmd.backend.services.conversion.pdf.cleaner.footnotes import FootnoteQueue
from clearmd.backend.services.conversion.pdf.cleaner.joining import joined
from clearmd.backend.services.conversion.pdf.cleaner.params import SENTENCE_END


class ParagraphBuffer:
    """Turns the block being built into a Markdown block; owns the blocks and the held notes."""

    def __init__(self, flow: Flow) -> None:
        self.flow = flow
        self.blocks: list[str] = []
        self.notes = FootnoteQueue()
        self.headings = 0

    def flush(self) -> None:
        """The block being built, written as a heading, a list item or a paragraph."""
        flow = self.flow
        if not flow.parts:
            flow.kind = ""
            return
        text = escape_text(joined(flow.parts))
        if flow.kind == "heading":
            self.blocks.append(f"{MARK}{'#' * flow.level} {heading_text(text)}")
            self.headings += 1
        elif flow.kind == "item":
            # "• # x" is no heading in an item (security audit of 008): what follows the
            # marker is neutralized like any line, its indentation (marks removed) dropped.
            self.blocks.append(f"{MARK}- " + neutralize(text.lstrip(), keep_marks=True))
        else:
            self.blocks.append(text)
        ended = flow.kind != "text" or bool(SENTENCE_END.search(flow.parts[-1]))
        kind = flow.kind
        flow.parts = []
        flow.kind = ""
        if kind != "heading" and ended:
            self.release()

    def release(self) -> None:
        """The held footnotes are written."""
        self.notes.release(self.blocks)
