"""Runs of text written with their delimiters opened and closed as the properties change.

One function, used by the writer and by the emphasis check (which replays it): its own module.
"""

from clearmd.backend.services.conversion.inline.delimiters import active, closer, opener
from clearmd.backend.services.conversion.inline.pieces import Text, split_space
from clearmd.backend.services.conversion.markdown_out import escape_text, inline_code, join_pieces


def styled(group: list[Text]) -> str:
    """Runs of text with their delimiters opened and closed as the properties change."""
    out: list[str] = []
    opened: list[str] = []
    pending: list[str] = []  # spaces between two runs, joined once
    for piece in group:
        lead, core, trail = split_space(piece.text)
        if not core:
            pending.append(piece.text)
            continue
        wanted = active(piece.props)
        keep = 0
        while keep < len(opened) and opened[keep] in wanted:
            keep += 1
        out.extend(closer(key) for key in reversed(opened[keep:]))
        opened = opened[:keep]
        out.append("".join(pending) + lead)
        pending.clear()
        for key in wanted:
            if key not in opened:
                out.append(opener(key))
                opened.append(key)
        out.append(inline_code(core) if piece.props.mono else escape_text(core))
        pending.append(trail)
    out.extend(closer(key) for key in reversed(opened))
    out.append("".join(pending))
    # The same joining rules as between pieces: a backtick of the text never glues to a code span.
    return join_pieces(out)
