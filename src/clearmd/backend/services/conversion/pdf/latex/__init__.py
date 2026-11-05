r"""A display equation rebuilt as LaTeX from where its pieces stand (feature 015, ADR-0036).

A PDF draws an equation as characters and lines: a fraction is a numerator above a short bar and a
denominator below it, a script is a smaller character raised or lowered, a sum's limits stand
above and below it, a tall bracket spans what it holds. Read back in that order, they make LaTeX:
``CEF_{o}^{t+1} = \frac{0e/0d}{0a/0b}``, shown as a formula by any viewer with math (VS Code,
GitHub, Obsidian) and copied as text.

Only what is understood is written: anything unexpected (a piece no rule places, a character that
cannot be read, a page of formulas) gives None, and the equation is written as before (its
picture, or its rows as text).

Pure: characters and bars in, a LaTeX string (or None) out.
"""

from clearmd.backend.services.conversion.pdf.latex.layout import MAX_ROWS
from clearmd.backend.services.conversion.pdf.latex.nodes import Bar, Glyph
from clearmd.backend.services.conversion.pdf.latex.writer import MAX_GLYPHS, to_latex

__all__ = ["MAX_GLYPHS", "MAX_ROWS", "Bar", "Glyph", "to_latex"]
