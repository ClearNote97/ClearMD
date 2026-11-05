"""Whitespace as HTML and ODF read it, and equal neighbours merged."""

import re

from clearmd.backend.services.conversion.inline.pieces import LINE_BREAK, Piece, Raw, Text

_WHITESPACE = re.compile(r"[ \t\r\n]+")


def normalize(pieces: list[Piece]) -> list[Piece]:
    """Whitespace as HTML and ODF read it: runs collapse to one space, none at the start or
    the end; equal neighbours are merged (their texts joined once: linear)."""
    cleaned: list[Piece] = []
    for piece in pieces:
        if isinstance(piece, Text) and not piece.literal:
            text = _WHITESPACE.sub(" ", piece.text)
            previous = cleaned[-1] if cleaned else None
            ends_in_space = (
                previous is None
                or (isinstance(previous, Raw) and previous.markdown == LINE_BREAK)
                or (isinstance(previous, Text) and previous.text.endswith(" "))
            )
            if ends_in_space:
                text = text.lstrip(" ")
            if not text:
                continue
            piece = Text(text, piece.props, piece.link)
        cleaned.append(piece)
    out: list[Piece] = []
    merged: list[str] = []  # the texts that make out[-1], joined when the run ends

    def close() -> None:
        last = out[-1] if out else None
        if merged and isinstance(last, Text):
            out[-1] = Text("".join(merged), last.props, last.link, literal=True)
        merged.clear()

    for piece in cleaned:
        last = out[-1] if out else None
        if (
            isinstance(piece, Text)
            and isinstance(last, Text)
            and (last.props, last.link) == (piece.props, piece.link)
        ):
            if not merged:
                merged.append(last.text)
            merged.append(piece.text)
            continue
        close()
        out.append(piece)
    close()
    while out and isinstance(out[-1], Text) and not out[-1].text.strip():
        out.pop()
    if out and isinstance(out[-1], Text):
        out[-1] = Text(out[-1].text.rstrip(" "), out[-1].props, out[-1].link, literal=True)
    return out
