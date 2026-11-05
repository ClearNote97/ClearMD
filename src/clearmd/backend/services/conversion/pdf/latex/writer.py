"""The equation as LaTeX, or None when any of it is unsure (feature 015)."""

from clearmd.backend.services.conversion.pdf.latex.envelope import balanced, without_label
from clearmd.backend.services.conversion.pdf.latex.layout import layout
from clearmd.backend.services.conversion.pdf.latex.nodes import Bar, Glyph, node_of
from clearmd.backend.services.conversion.pdf.latex.unsure import Unsure

MAX_GLYPHS = 600  # an equation's characters at most: more is a page of formulas, not one
MAX_BARS = 64  # an equation's drawn lines at most: more is a drawing, not a formula
UNREADABLE = "�"


def to_latex(glyphs: list[Glyph], bars: list[Bar]) -> str | None:
    """The equation as LaTeX (its number as ``\\tag``), or None when any of it is unsure."""
    if not glyphs or len(glyphs) > MAX_GLYPHS or len(bars) > MAX_BARS:
        return None
    if any(UNREADABLE in glyph.text for glyph in glyphs):
        return None
    glyphs, tag = without_label(glyphs)
    if not glyphs:
        return None
    try:
        body = layout([node_of(glyph) for glyph in glyphs], list(bars), 0)
    except (Unsure, ValueError, ZeroDivisionError, RecursionError):
        return None  # unsure is never a failure: the equation is written as before
    if not body.strip():
        return None
    latex = f"{body} \\tag{{{tag}}}" if tag else body
    return latex if balanced(latex) else None
