"""Leaf elements (``mi``, ``mn``, ``mo``) and the pieces of LaTeX that glue the results together."""

import re

from clearmd.backend.services.conversion.odt.mathml.attributes import element_text
from clearmd.backend.services.conversion.odt.mathml.tables import (
    FUNCTIONS,
    GREEK,
    LATEX_SPECIAL,
    SYMBOLS,
    WORDS,
)
from clearmd.backend.services.conversion.xmltree import Element

CONTROL_WORD_END = re.compile(r"\\[A-Za-z]+$")


def char(char: str, table: dict[str, str]) -> str:
    if char in GREEK:
        return f"\\{GREEK[char]}"
    if char in SYMBOLS:
        return SYMBOLS[char]
    return table.get(char, char)


def join(parts: list[str]) -> str:
    """Pieces of LaTeX in order; a control word never glues to the letter after it. Linear:
    only the end of the previous piece is looked at."""
    out: list[str] = []
    for part in parts:
        if not part:
            continue
        if out and part[0].isalpha() and CONTROL_WORD_END.search(out[-1][-64:]):
            out.append(" ")
        out.append(part)
    return "".join(out)


def group(latex: str) -> str:
    return f"{{{latex}}}"


def identifier(element: Element) -> str:
    text = element_text(element)
    variant = element.get("mathvariant")
    if text in WORDS:
        return WORDS[text]
    if text in FUNCTIONS:
        return f"\\{text}"
    if len(text) == 1:
        letter = char(text, LATEX_SPECIAL)
    else:
        letter = "".join(char(c, LATEX_SPECIAL) for c in text)
    if variant == "bold":
        return f"\\mathbf{{{letter}}}"
    if variant == "normal" and len(text) > 1 and text.isalpha():
        return f"\\mathrm{{{letter}}}"
    return letter


def operator(element: Element) -> str:
    text = element_text(element)
    if text in WORDS:
        return WORDS[text]
    return "".join(char(c, LATEX_SPECIAL) for c in text)
