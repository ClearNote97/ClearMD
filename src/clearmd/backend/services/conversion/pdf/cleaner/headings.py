"""Headings: their patterns, the level of a line, and how a heading starts, goes on or is cut.

Also a table of contents' entry and the caption pattern, which start blocks of their own
(008, 013).
"""

import re

from clearmd.backend.services.conversion.pdf.cleaner.buffer import ParagraphBuffer
from clearmd.backend.services.conversion.pdf.cleaner.flow import Flow, is_short, sentence_ended
from clearmd.backend.services.conversion.pdf.cleaner.params import MAX_LEVEL
from clearmd.backend.services.conversion.pdf.cleaner.sizes import heading_like, size_key
from clearmd.backend.services.conversion.pdf.model import Line

MAX_HEADING_LINES = 3  # a heading wrapped on several lines is one heading; more is a paragraph
# A table of contents' entry ends with its page, after leaders: "Encuesta ....... 16" (013).
_TOC_PAGE = re.compile(r"(?<![\w])(?:\d{1,5}|[ivxlcdm]{1,8}|[IVXLCDM]{1,8})$")
# A table's or a figure's caption starts its own block (013): "Table 3: …", "Figura 2. …".
CAPTION = re.compile(
    r"(?:Table|Tabla|Cuadro|Figure|Figura|Fig\.|Gráfico|Gráfica|Ilustración)\s+[0-9IVXLC]+[.:]\s"
)
# "2 Methodology", "3.1 Data", "IV. RESULTADOS": numbered, then a capital (or "¿").
NUMBERED = re.compile(r"(?:(\d{1,2}(?:\.\d{1,2}){0,3})\.?|([IVXL]{1,5})\.)\s+[A-ZÁÉÍÓÚÑ¿]")
INSIDE_SENTENCE = re.compile(r"[.?!]\s+\S|=")


def toc_entry(text: str) -> bool:
    """A table of contents' entry: its leaders, then its page ("Encuesta ....... 16"). Read from
    the end of the line, never a pattern over it (a line of dots costs nothing; review of 013)."""
    stripped = text.rstrip()
    found = _TOC_PAGE.search(stripped[-12:])
    if found is None:
        return False
    before = stripped[: len(stripped) - len(found.group())].rstrip()
    return before.endswith(("....", "……", ". . . ."))


def heading_level(flow: Flow, levels: dict[float, int], line: Line, gap: bool) -> int:
    """The level of the heading the line is; 0 when it is not one."""
    if not heading_like(line):
        return 0
    found = levels.get(size_key(line.size))
    if found:
        return found
    numbered = NUMBERED.match(line.text)
    # A bold number starts a heading only where a block may start: a page's top, a blank,
    # after a sentence's end or another block; never in the middle of a paragraph.
    starts = flow.last is None or gap or flow.kind != "text" or sentence_ended(flow)
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


def heading(
    buffer: ParagraphBuffer, levels: dict[float, int], line: Line, level: int, gap: bool
) -> None:
    """The line starts a heading, or goes on with the one being built."""
    flow = buffer.flow
    same = flow.kind == "heading" and level == flow.level and not gap
    if same and len(flow.parts) >= MAX_HEADING_LINES:
        flow.kind, flow.grown = "text", True  # four lines: a paragraph, not a heading
        flow.parts.append(line.text)
        return
    if not same:
        buffer.flush()
        buffer.release()  # footnotes before a heading, never between it and its text
        flow.kind, flow.level = "heading", level
        flow.numbered = levels.get(size_key(line.size)) is None
    flow.parts.append(line.text)


def cut_sentence(flow: Flow, line: Line, gap: bool, resized: bool) -> bool:
    """The line after a bold numbered "heading" goes on in lowercase, close and in the same
    size: that was the start of a sentence, not a heading (adversarial check of 008)."""
    return (
        flow.kind == "heading"
        and not gap
        and not resized
        and line.text[:1].islower()
        and not line.bold
    )


def heading_goes_on(flow: Flow, line: Line, gap: bool, resized: bool) -> bool:
    """The second line of a bold numbered heading: bold too, same size, close, after a first
    line that filled the width or before one in lowercase (a short heading is whole; the bold
    line after it is text)."""
    last = flow.last
    return (
        flow.kind == "heading"
        and last is not None
        and last.bold
        and (not is_short(flow, last) or line.text[:1].islower())  # or it goes on in lowercase
        and line.bold
        and not gap
        and not resized
        and len(flow.parts) < MAX_HEADING_LINES
        and heading_like(line)
    )
