"""Math written back as the author wrote it, with the author's macros expanded."""

from typing import Any

from clearmd.backend.services.conversion.tex.nodes import is_macro


def is_label(node: Any) -> bool:
    """Whether ``node`` is a ``\\label``, which math drops."""
    return is_macro(node, "label")
