"""A row's pieces, joined: words as words, a space where there was one (feature 015)."""

import re

from clearmd.backend.services.conversion.pdf.latex.nodes import Node
from clearmd.backend.services.conversion.pdf.latex.scripts import with_scripts
from clearmd.backend.services.conversion.pdf.latex.symbols import BIG_OPERATORS

SPACE = 0.18  # of the text's size: a gap this wide between pieces is written as a space
QUAD = 1.2  # of the text's size: a gap this wide is written as a quad
WORD_LETTERS = 4  # lowercase letters in a row, with a vowel: a word ("produce")
_FUNCTIONS = frozenset(
    "sin cos tan cot sec csc arcsin arccos arctan sinh cosh tanh log ln lg exp det dim ker "
    "deg gcd hom arg max min sup inf lim liminf limsup Pr".split()
)
_OPERATOR_WORDS = frozenset("Max Min Sup Inf Lim argmax argmin Argmax Argmin".split())
_WORDS = frozenset(
    "if for and or otherwise where with such that si para donde con subject to sujeto can the "
    "all any are not has let set its per una los las del por que".split()
)


def row_text(row: list[Node], size: float) -> str:
    """A row's pieces, joined: words as words ("Max", "if"), a space where there was one."""
    out: list[str] = []
    index = 0
    previous: Node | None = None
    while index < len(row):
        end = index
        while (
            end + 1 < len(row)
            and _letter(row[end]) and _letter(row[end + 1])
            and not ({"^", "_"} & row[end].scripts.keys())
            and row[end + 1].left - row[end].right <= SPACE * size
        ):  # fmt: skip
            end += 1
        word = "".join(node.char for node in row[index : end + 1])
        last = row[end]
        prose = word in _WORDS or _a_word(word)
        if end > index and (word in _FUNCTIONS or word in _OPERATOR_WORDS or prose):
            limits: dict[str, str] = {}
            for node in row[index : end + 1]:
                for kind, latex in node.scripts.items():
                    limits[kind] = f"{limits[kind]} {latex}" if kind in limits else latex
            if word in _FUNCTIONS:
                piece = "\\" + word
            elif word in _OPERATOR_WORDS:
                piece = rf"\operatorname*{{{word}}}"
            else:
                piece = rf"\text{{ {word} }}"
            piece = with_scripts(piece, limits, operator=not prose)
        else:
            end = index
            node = row[index]
            piece = with_scripts(node.latex, node.scripts, operator=node.char in BIG_OPERATORS)
            last = node
        first = row[index]
        if previous is not None:
            gap = first.left - max(previous.right, previous.reach)
            if gap > QUAD * size:
                out.append(r" \quad ")  # set apart on the page: "x_{n} \quad n = 1, …"
            else:
                out.append(" " if gap > SPACE * size or _glued(out[-1], piece) else "")
        out.append(piece)
        previous = last
        index = end + 1
    return "".join(out)


def _a_word(word: str) -> bool:
    """A word of the text inside the equation ("x can produce y"): four lowercase letters or
    more, with a vowel ("abc", "ijk" are products of variables)."""
    return len(word) >= WORD_LETTERS and word.islower() and any(c in "aeiou" for c in word)


def _letter(node: Node) -> bool:
    return len(node.char) == 1 and node.char.isalpha() and node.char.isascii()


def _glued(before: str, after: str) -> bool:
    """A command followed by a letter needs a space between them (``\\theta y``)."""
    return re.search(r"\\[A-Za-z]+$", before) is not None and after[:1].isalpha()
