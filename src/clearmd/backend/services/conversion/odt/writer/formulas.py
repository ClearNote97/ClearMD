"""Formulas: the Markdown of a formula object, display math included."""

from clearmd.backend.services.conversion.markdown_out import MARK, math_line


def display_math(latex: str) -> str:
    """``$$`` lines are ClearMD's; the math between them is never read as Markdown blocks."""
    lines = "\n".join(math_line(line) for line in latex.split("\n"))
    return f"{MARK}$$\n{lines}\n{MARK}$$"
