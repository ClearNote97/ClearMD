"""Inline text as ClearMD writes it, shared by its own converters (``.odt``, the HTML article
mode): runs of text with their properties, joined and escaped through ``markdown_out``, with
emphasis Markdown can hold only (an exact check of CommonMark's emphasis algorithm), links by the
rules of ADR-0023, and a growth budget for what a link repeats. Standard library only."""

from clearmd.backend.services.conversion.inline.commonmark import unpaired_delimiters
from clearmd.backend.services.conversion.inline.pieces import (
    IMAGE_WORD,
    LINE_BREAK,
    Piece,
    Raw,
    Text,
    TextProps,
)
from clearmd.backend.services.conversion.inline.writer import InlineWriter

__all__ = [
    "IMAGE_WORD",
    "LINE_BREAK",
    "InlineWriter",
    "Piece",
    "Raw",
    "Text",
    "TextProps",
    "unpaired_delimiters",
]
