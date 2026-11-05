"""Footnotes: a note takes its number first, its definition is kept for the document's end.

It stands alone because a note holds paragraphs of its own, which come back through ``w.inline``.
"""

from clearmd.backend.services.conversion.inline import LINE_BREAK
from clearmd.backend.services.conversion.odt.writer.paragraphs import (
    hidden,
    own_paragraphs,
    paragraph_props,
)
from clearmd.backend.services.conversion.odt.writer.state import Writer
from clearmd.backend.services.conversion.odt.writer.vocab import MAX_NOTES
from clearmd.backend.services.conversion.xmltree import Element


def note_reference(w: Writer, note: Element) -> str:
    if len(w.state.footnotes) >= MAX_NOTES:
        w.state.note_unknown("text:note")
        return ""
    number = len(w.state.footnotes) + 1
    w.state.footnotes.append("")  # its number is taken before notes nested in it get theirs
    body = note.find("text:note-body")
    paragraphs = own_paragraphs(w, body) if body is not None else []
    shown = [p for p in paragraphs if not hidden(w, p)]
    texts = [w.inline(p, paragraph_props(w, p)).replace(LINE_BREAK, " ") for p in shown]
    # An empty definition would not be one: the reference would show as text.
    w.state.footnotes[number - 1] = " ".join(text for text in texts if text) or "…"
    return f"[^{number}]"
