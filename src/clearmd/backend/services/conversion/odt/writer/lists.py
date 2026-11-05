"""Lists: numbering and nesting of ``text:list``."""

from clearmd.backend.services.conversion.xmltree import Element


def continues_numbering(element: Element) -> bool:
    return element.get("text:continue-numbering") == "true" or bool(
        element.get("text:continue-list")
    )
