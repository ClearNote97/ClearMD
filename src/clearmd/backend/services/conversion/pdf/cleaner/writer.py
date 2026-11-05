"""Blocks in order: headings, list items and paragraphs, each one Markdown block (008)."""

from clearmd.backend.services.conversion.pdf.cleaner.buffer import ParagraphBuffer
from clearmd.backend.services.conversion.pdf.cleaner.flow import (
    Flow,
    has_gap,
    is_short,
    paragraph_ended,
    set_typical,
)
from clearmd.backend.services.conversion.pdf.cleaner.headings import (
    CAPTION,
    cut_sentence,
    heading,
    heading_goes_on,
    heading_level,
    toc_entry,
)
from clearmd.backend.services.conversion.pdf.cleaner.items import list_item
from clearmd.backend.services.conversion.pdf.cleaner.joining import is_resized
from clearmd.backend.services.conversion.pdf.cleaner.params import SENTENCE_END
from clearmd.backend.services.conversion.pdf.cleaner.render import block_markdown
from clearmd.backend.services.conversion.pdf.model import Line


class Writer:
    """Blocks in order: headings, list items and paragraphs, each one Markdown block."""

    def __init__(self, body: float, levels: dict[float, int]) -> None:
        self._body = body
        self._levels = levels
        self.flow = Flow()
        self.buffer = ParagraphBuffer(self.flow)

    def hold(self, notes: list[Line]) -> None:
        """A page's footnotes: one block each, after the paragraph the page break cut."""
        self.buffer.notes.hold(notes)
        if not self.flow.parts:  # nothing waits for the next page: they go now
            self.buffer.release()

    def page_break(self) -> None:
        """A paragraph goes on to the next page only when its sentence does; a heading or a list
        item ends with its page."""
        ended = self.flow.parts and SENTENCE_END.search(self.flow.parts[-1])
        if self.flow.kind == "heading" or ended:
            self.buffer.flush()
        self.flow.last = None

    # --- Lines -----------------------------------------------------------------------------

    def add(self, line: Line) -> None:
        """One more line, in the page's order."""
        block = block_markdown(line)
        if block is not None:  # a table, an equation, a picture: its own block (012, 013)
            self.buffer.flush()  # after the text above it, in the page's order (review of 013)
            self.buffer.blocks.append(block)
            self.flow.last = None  # no gap is measured from a block
            return
        if CAPTION.match(line.text):  # "Table 3: …": its own paragraph, its table after it
            self.buffer.flush()
            self.flow.kind = "text"
            self.flow.parts.append(line.text)
            self.flow.last = line
            return
        entry = toc_entry(line.text)
        last = self.flow.last
        if entry and self.flow.kind == "text" and last is not None and is_short(self.flow, last):
            self.buffer.flush()  # its title ("Índice") above the first entry, in the body's size
        self._text(line)
        if entry and self.flow.kind == "text":
            self.buffer.flush()  # a table of contents: one entry per line (013)

    def _text(self, line: Line) -> None:
        flow = self.flow
        gap = has_gap(flow, line)
        last = flow.last
        resized = last is not None and is_resized(last, line)
        level = heading_level(flow, self._levels, line, gap)
        if flow.kind == "text" and flow.grown and not gap and not resized:
            flow.parts.append(line.text)  # a paragraph in a larger font goes on
        elif flow.numbered and cut_sentence(flow, line, gap, resized):
            flow.kind, flow.numbered = "text", False  # "15 Juzgados … que" + "completan": text
            flow.grown = False
            flow.parts.append(line.text)
        elif level:
            heading(self.buffer, self._levels, line, level, gap)
        elif heading_goes_on(flow, line, gap, resized):
            flow.parts.append(line.text)
        elif item := list_item(flow, line):
            self.buffer.flush()
            flow.kind = "item"
            flow.parts.append(item)
        else:
            lower = line.text[:1].islower()
            new = flow.parts and not lower and paragraph_ended(flow)
            ends_item = flow.kind == "item" and not lower  # an item goes on only in lowercase
            if flow.kind in {"heading", ""} or gap or resized or new or ends_item:
                self.buffer.flush()
            if not flow.kind:
                flow.kind = "text"
                flow.grown = False
            flow.parts.append(line.text)
        flow.last = line

    def set_typical(self, lines: list[Line]) -> None:
        """A full line's length on this page."""
        set_typical(self.flow, lines)

    def finish(self) -> str:
        """The last block written and the footnotes still held: all the blocks, as one text."""
        self.buffer.flush()
        self.buffer.release()
        return "\n\n".join(self.buffer.blocks)
