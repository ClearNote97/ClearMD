"""Blocks in order: headings, list items and paragraphs, each one Markdown block (008)."""

from clearmd.backend.services.conversion.markdown_out import (
    MARK,
    escape_text,
    heading_text,
    neutralize,
)
from clearmd.backend.services.conversion.pdf.cleaner.footnotes import NOTE_START
from clearmd.backend.services.conversion.pdf.cleaner.headings import (
    CAPTION,
    INSIDE_SENTENCE,
    MAX_HEADING_LINES,
    NUMBERED,
    toc_entry,
)
from clearmd.backend.services.conversion.pdf.cleaner.items import BULLET, CIRCLE, DASH
from clearmd.backend.services.conversion.pdf.cleaner.joining import is_resized, joined
from clearmd.backend.services.conversion.pdf.cleaner.params import (
    MAX_LEVEL,
    PARAGRAPH_GAP,
    SENTENCE_END,
)
from clearmd.backend.services.conversion.pdf.cleaner.render import block_markdown
from clearmd.backend.services.conversion.pdf.cleaner.sizes import heading_like, size_key
from clearmd.backend.services.conversion.pdf.model import Line


class Writer:
    """Blocks in order: headings, list items and paragraphs, each one Markdown block."""

    def __init__(self, body: float, levels: dict[float, int]) -> None:
        self._body = body
        self._levels = levels
        self.blocks: list[str] = []
        self._kind = ""  # "", "heading", "item", "text"
        self._parts: list[str] = []
        self._last: Line | None = None
        self._level = 0
        self._typical = 80.0  # a full line's length on this page, in characters
        self._held: list[str] = []  # footnotes, written once the paragraph they cut ends
        self.headings = 0

    # --- Blocks ----------------------------------------------------------------------------

    def _flush(self) -> None:
        if not self._parts:
            self._kind = ""
            return
        text = escape_text(joined(self._parts))
        if self._kind == "heading":
            self.blocks.append(f"{MARK}{'#' * self._level} {heading_text(text)}")
            self.headings += 1
        elif self._kind == "item":
            # "• # x" is no heading in an item (security audit of 008): what follows the
            # marker is neutralized like any line, its indentation (marks removed) dropped.
            self.blocks.append(f"{MARK}- " + neutralize(text.lstrip(), keep_marks=True))
        else:
            self.blocks.append(text)
        ended = self._kind != "text" or bool(SENTENCE_END.search(self._parts[-1]))
        kind = self._kind
        self._parts = []
        self._kind = ""
        if kind != "heading" and ended:
            self._release()

    def _release(self) -> None:
        self.blocks.extend(self._held)
        self._held = []

    def hold(self, notes: list[Line]) -> None:
        """A page's footnotes: one block each, after the paragraph the page break cut."""
        parts: list[str] = []
        for line in notes:
            if parts and NOTE_START.match(line.text):
                self._held.append(escape_text(joined(parts)))
                parts = []
            parts.append(line.text)
        if parts:
            self._held.append(escape_text(joined(parts)))
        if not self._parts:  # nothing waits for the next page: they go now
            self._release()

    def page_break(self) -> None:
        """A paragraph goes on to the next page only when its sentence does; a heading or a list
        item ends with its page."""
        ended = self._parts and SENTENCE_END.search(self._parts[-1])
        if self._kind == "heading" or ended:
            self._flush()
        self._last = None

    # --- Lines -----------------------------------------------------------------------------

    def add(self, line: Line) -> None:
        block = block_markdown(line)
        if block is not None:  # a table, an equation, a picture: its own block (012, 013)
            self._flush()  # after the text above it, in the page's order (review of 013)
            self.blocks.append(block)
            self._last = None  # no gap is measured from a block
            return
        if CAPTION.match(line.text):  # "Table 3: …": its own paragraph, its table after it
            self._flush()
            self._kind = "text"
            self._parts.append(line.text)
            self._last = line
            return
        entry = toc_entry(line.text)
        last = self._last
        if entry and self._kind == "text" and last is not None and self._short(last):
            self._flush()  # its title ("Índice") above the first entry, in the body's size
        self._text(line)
        if entry and self._kind == "text":
            self._flush()  # a table of contents: one entry per line (013)

    def _text(self, line: Line) -> None:
        gap = self._gap(line)
        last = self._last
        resized = last is not None and is_resized(last, line)
        level = self._heading_level(line, gap)
        if self._kind == "text" and self._grown and not gap and not resized:
            self._parts.append(line.text)  # a paragraph in a larger font goes on
        elif self._numbered and self._cut_sentence(line, gap, resized):
            self._kind, self._numbered = "text", False  # "15 Juzgados … que" + "completan": text
            self._grown = False
            self._parts.append(line.text)
        elif level:
            self._heading(line, level, gap)
        elif self._heading_goes_on(line, gap, resized):
            self._parts.append(line.text)
        elif item := self._item(line):
            self._flush()
            self._kind = "item"
            self._parts.append(item)
        else:
            lower = line.text[:1].islower()
            new = self._parts and not lower and self._ended()
            ends_item = self._kind == "item" and not lower  # an item goes on only in lowercase
            if self._kind in {"heading", ""} or gap or resized or new or ends_item:
                self._flush()
            if not self._kind:
                self._kind = "text"
                self._grown = False
            self._parts.append(line.text)
        self._last = line

    _grown = False  # the paragraph started as a heading: a larger font, too long for one
    _numbered = False  # the heading came from a bold number, not from its size

    def _heading(self, line: Line, level: int, gap: bool) -> None:
        same = self._kind == "heading" and level == self._level and not gap
        if same and len(self._parts) >= MAX_HEADING_LINES:
            self._kind, self._grown = "text", True  # four lines: a paragraph, not a heading
            self._parts.append(line.text)
            return
        if not same:
            self._flush()
            self._release()  # footnotes before a heading, never between it and its text
            self._kind, self._level = "heading", level
            self._numbered = self._levels.get(size_key(line.size)) is None
        self._parts.append(line.text)

    def _cut_sentence(self, line: Line, gap: bool, resized: bool) -> bool:
        """The line after a bold numbered "heading" goes on in lowercase, close and in the same
        size: that was the start of a sentence, not a heading (adversarial check of 008)."""
        return (
            self._kind == "heading"
            and not gap
            and not resized
            and line.text[:1].islower()
            and not line.bold
        )

    def _heading_goes_on(self, line: Line, gap: bool, resized: bool) -> bool:
        """The second line of a bold numbered heading: bold too, same size, close, after a first
        line that filled the width or before one in lowercase (a short heading is whole; the bold
        line after it is text)."""
        last = self._last
        return (
            self._kind == "heading"
            and last is not None
            and last.bold
            and (not self._short(last) or line.text[:1].islower())  # or it goes on in lowercase
            and line.bold
            and not gap
            and not resized
            and len(self._parts) < MAX_HEADING_LINES
            and heading_like(line)
        )

    def _item(self, line: Line) -> str | None:
        text = line.text
        if bullet := BULLET.match(text):
            return text[bullet.end() :]
        mid_sentence = self._kind == "text" and not self._ended_sentence()
        if (dash := DASH.match(text)) and not mid_sentence:
            return text[dash.end() :]
        if (circle := CIRCLE.match(text)) and self._kind == "item":
            return text[circle.end() :]
        return None

    def _ended_sentence(self) -> bool:
        return bool(self._parts) and bool(SENTENCE_END.search(self._parts[-1]))

    def _ended(self) -> bool:
        """The previous line ended a sentence and the next one starts a new one with a capital:
        a paragraph ends there only if that line was short (the rest of it was left blank)."""
        last = self._last
        return last is not None and bool(SENTENCE_END.search(last.text)) and self._short(last)

    def _short(self, line: Line) -> bool:
        return len(line.text) < 0.6 * self._typical

    def set_typical(self, lines: list[Line]) -> None:
        lengths = sorted(len(line.text) for line in lines)
        self._typical = float(lengths[len(lengths) * 3 // 4]) if lengths else 80.0

    def _gap(self, line: Line) -> bool:
        last = self._last
        if last is None:
            return False
        height = max(min(last.size, line.size), 1.0)
        blank = last.bottom - line.top
        return blank > PARAGRAPH_GAP * height or line.top > last.top + height  # or a new column

    def _heading_level(self, line: Line, gap: bool) -> int:
        if not heading_like(line):
            return 0
        found = self._levels.get(size_key(line.size))
        if found:
            return found
        numbered = NUMBERED.match(line.text)
        # A bold number starts a heading only where a block may start: a page's top, a blank,
        # after a sentence's end or another block; never in the middle of a paragraph.
        starts = self._last is None or gap or self._kind != "text" or self._ended_sentence()
        if (
            not starts
            or not line.bold
            or numbered is None
            or len(line.text) > 90
            or INSIDE_SENTENCE.search(line.text, numbered.end())
        ):
            return 0
        arabic = numbered.group(1)
        return min(arabic.count(".") + 2, MAX_LEVEL) if arabic else 2

    def finish(self) -> str:
        self._flush()
        self._release()
        return "\n\n".join(self.blocks)
