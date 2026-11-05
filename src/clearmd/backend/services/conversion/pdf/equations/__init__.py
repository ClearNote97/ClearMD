"""Display equations in a PDF page, found by their number (feature 013, ADR-0034).

A displayed equation is set apart, with its number at the right margin: "(5)" alone on its row or
far from the formula before it. Its lines are the short ones of symbols around that number, up to
the prose before and after it. PDFium gives them as scattered pieces ("∑", "J", "j=1"); kept
together they are either cropped from the page as a picture (with the images folder, ADR-0033) or
written as a block that keeps their lines.

Pure: lines and words in, the equations' line ranges out.
"""

from clearmd.backend.services.conversion.pdf.equations.find import find_equations
from clearmd.backend.services.conversion.pdf.equations.model import Placed

__all__ = ["Placed", "find_equations"]
