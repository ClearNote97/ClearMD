"""Formulas: the Markdown of a formula object (inline or display), within the growth budget.

It stands alone because both paragraphs (display math) and frames (inline math) write formulas.
"""

from clearmd.backend.services.conversion.markdown_out import (
    MARK,
    escape_math,
    inline_code,
    math_line,
)
from clearmd.backend.services.conversion.odt.writer.state import FormulaResult, Writer
from clearmd.backend.services.conversion.xmltree import Element


def formula_markdown(w: Writer, formula: Element, *, display: bool) -> str | None:
    """The formula's Markdown; ``None`` when the object is not a formula at all."""
    found = w.state.formula(formula) if w.state.formula is not None else FormulaResult(None)
    if not found.formula:
        return None
    if found.latex is not None and not found.latex.strip():
        return ""  # an empty formula: nothing to show, never a stray "$$"
    if found.latex is not None and not w.state.spend(len(found.latex)):
        found = FormulaResult(None, found.source)  # past the growth budget
    if found.latex is None:
        w.state.counts.formulas_kept += 1
        if found.source and w.state.spend(len(found.source)):  # the source is charged too
            return inline_code(found.source)
        return f"*{w.state.formula_word}*"
    latex = escape_math(found.latex)
    return display_math(latex) if display else f"${latex}$"


def display_math(latex: str) -> str:
    """``$$`` lines are ClearMD's; the math between them is never read as Markdown blocks."""
    lines = "\n".join(math_line(line) for line in latex.split("\n"))
    return f"{MARK}$$\n{lines}\n{MARK}$$"
