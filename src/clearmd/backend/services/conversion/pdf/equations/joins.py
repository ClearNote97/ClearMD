"""Whether a line belongs to an equation: no prose, no heading, no caption, close by (013)."""

import re

from clearmd.backend.services.conversion.pdf.equations.model import Placed

GAP_EMS = 5.0  # a blank this tall (in line heights) above or below what is found ends it
TITLE_RATIO = 1.15  # a line this much larger than the equation's number is a heading
TITLE_LETTERS = 3  # if it has words: a tall "{" or "∑" alone is not
_CAPTION = re.compile(r"(?:Table|Tabla|Cuadro|Figure|Figura|Fig\.)\s+[0-9IVXLC]+\b")
_NUMBERED_HEADING = re.compile(r"\d{1,2}(?:\.\d{1,2})*\.?\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]")
PROSE_WORDS = 3  # a line with this many words of four letters or more is prose
_WORD = re.compile(r"\b[a-záéíóúüñ]{4,}\b")
# With no number to hold it, capitalised words make prose too ("Index", "Equation"); a numbered
# equation may name its variables so ("Profit = Revenue - Costs", review of 015).
_ANY_WORD = re.compile(r"\b[a-záéíóúüñ]{4,}\b", re.I)
# A line that starts a clause goes on the text: "where zj are …", "donde x es …".
_LEADS = re.compile(r"(?:where|donde|with|which|for|para|subject|sujeto)\s", re.I)  # not "y"


def joins(
    line: Placed, index: int, box: list[float], stops: set[int], unnumbered: bool = False
) -> bool:
    """Whether the line is one of the equation's: a line of symbols near what is found (its
    number may stand halfway down it); ``box`` grows with it. A heading or a caption is not."""
    if index in stops or line.other or prose(line.text, unnumbered) or titled(line, box[2]):
        return False
    reach = GAP_EMS * max(line.size, box[2], 1.0)
    if line.bottom - box[1] > reach or box[0] - line.top > reach:
        return False
    box[0], box[1] = min(box[0], line.bottom), max(box[1], line.top)
    return True


def titled(line: Placed, size: float) -> bool:
    """A heading ("3. Methods", or words larger than the equation's number) or a caption. A tall
    brace, bracket or sum is the equation's own: no words (v0.8.0 cut equations there)."""
    text = line.text.strip()
    return (
        (line.size > TITLE_RATIO * size and sum(char.isalpha() for char in text) >= TITLE_LETTERS)
        or _CAPTION.match(text) is not None
        or _NUMBERED_HEADING.match(text) is not None
    )


def prose(text: str, any_case: bool = False) -> bool:
    """A line of sentences: several words, or one that leads into what follows ("as follows:")."""
    stripped = text.strip()
    return (
        len((_ANY_WORD if any_case else _WORD).findall(stripped)) >= PROSE_WORDS
        or stripped.endswith(":")
        or _LEADS.match(stripped) is not None
    )
