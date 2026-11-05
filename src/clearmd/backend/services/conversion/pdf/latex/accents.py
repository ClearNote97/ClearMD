"""An accent drawn over a letter, put on the piece below it (feature 015)."""

from clearmd.backend.services.conversion.pdf.latex.nodes import Node
from clearmd.backend.services.conversion.pdf.latex.symbols import ACCENTS
from clearmd.backend.services.conversion.pdf.latex.unsure import Unsure


def accents(nodes: list[Node], size: float) -> list[Node]:
    """Each accent on the piece right below it (``\\hat{\\beta}``); one with nothing below it
    is unsure."""
    accents = [node for node in nodes if node.char in ACCENTS]
    if not accents:
        return nodes
    for accent in accents:
        below = [
            node for node in nodes
            if node.char not in ACCENTS
            and node.left - 0.25 * size <= accent.middle_x <= node.right + 0.25 * size
            and node.middle < accent.middle and node.top <= accent.bottom + 0.4 * size
        ]  # fmt: skip
        if not below:
            raise Unsure
        base = max(below, key=lambda node: node.top)
        base.latex = f"{accent.latex}{{{base.latex}}}"
        base.char = ""  # no longer a plain letter of a word
    return [node for node in nodes if node.char not in ACCENTS]
