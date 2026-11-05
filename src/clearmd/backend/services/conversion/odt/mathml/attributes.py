"""What the translator reads off a MathML element, and the error for what it cannot translate."""

from clearmd.backend.services.conversion.odt.mathml.tables import FENCES
from clearmd.backend.services.conversion.xmltree import Element

MAX_DEPTH = 64
STARMATH = "StarMath 5.0"


class Unsupported(Exception):
    """A MathML construct outside ClearMD's subset: the formula keeps its StarMath source."""


def element_text(element: Element) -> str:
    return " ".join(element.text().split())


def children(element: Element) -> list[Element]:
    return list(element.elements())


def fence_char(element: Element) -> str | None:
    if element.tag != "math:mo" or element.get("fence") != "true":
        return None
    if element.get("stretchy") == "false":
        return None
    return FENCES.get(element_text(element))
