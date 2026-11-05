"""Pieces → Markdown: groups of text styled, links written by the rules of ADR-0023."""

import html
from collections.abc import Callable

from clearmd.backend.services.conversion.inline.commonmark import unpaired_delimiters
from clearmd.backend.services.conversion.inline.delimiters import EMPHASIS, without
from clearmd.backend.services.conversion.inline.emphasis import safe_emphasis
from clearmd.backend.services.conversion.inline.normalize import normalize
from clearmd.backend.services.conversion.inline.pieces import Piece, Text, split_space
from clearmd.backend.services.conversion.inline.styled import styled
from clearmd.backend.services.conversion.markdown_out import (
    SAFE_LINK,
    escape_text,
    inline_code,
    join_pieces,
    link_target,
)


class InlineWriter:
    """Pieces → Markdown. ``spend`` charges what a link's address repeats to the document's growth
    budget; ``dropped`` counts the runs whose emphasis Markdown could not hold (for a note)."""

    def __init__(self, spend: Callable[[int], bool]) -> None:
        self._spend = spend
        self.dropped = 0

    def normalize(self, pieces: list[Piece]) -> list[Piece]:
        """Whitespace as HTML and ODF read it (see ``normalize``): the module function."""
        return normalize(pieces)

    def write(self, pieces: list[Piece]) -> str:
        parts: list[str] = []
        index = 0
        while index < len(pieces):
            piece = pieces[index]
            if isinstance(piece, Text) and piece.link is not None:
                group = [piece]
                while (
                    index + 1 < len(pieces)
                    and isinstance(pieces[index + 1], Text)
                    and pieces[index + 1].link == piece.link  # type: ignore[union-attr]
                ):
                    index += 1
                    group.append(pieces[index])  # type: ignore[arg-type]
                parts.append(self._link(piece.link, group))
            elif isinstance(piece, Text):
                group = [piece]
                while (
                    index + 1 < len(pieces)
                    and isinstance(pieces[index + 1], Text)
                    and pieces[index + 1].link is None  # type: ignore[union-attr]
                ):
                    index += 1
                    group.append(pieces[index])  # type: ignore[arg-type]
                parts.append(self.style(group))
            else:
                parts.append(piece.markdown)
            index += 1
        return join_pieces(parts)

    def style(self, group: list[Text]) -> str:
        safe, dropped = safe_emphasis(group)
        written = styled(safe)
        if unpaired_delimiters(written):  # the pairing itself fails (CommonMark's rule of 3…)
            plain = [Text(p.text, without(p.props, set(EMPHASIS)), p.link, p.literal) for p in safe]
            dropped += sum(
                1 for old, new in zip(safe, plain, strict=True) if old.props != new.props
            )
            written = styled(plain)
        self.dropped += dropped
        return written

    def _link(self, url: str, group: list[Text]) -> str:
        written = self.style([Text(g.text, g.props, None, g.literal) for g in group])
        lead, text, trail = split_space(written)  # the spaces around the text stay outside the link
        url = url.strip()
        # Each piece of a link repeats its address: charged, and past the budget only the text.
        if not url or not self._spend(len(url)):
            return written
        # javascript: never becomes a link, written as it is or with entities ("&colon;"), even
        # though link_target keeps them from being decoded (a viewer might).
        if not SAFE_LINK.match(url) or not SAFE_LINK.match(html.unescape(url)):
            shown = f"{text} ({inline_code(url)})" if text else inline_code(url)
        else:
            shown = f"[{text or escape_text(url)}]({link_target(url)})"
        return lead + shown + trail
