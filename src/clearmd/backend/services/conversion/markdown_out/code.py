"""Code spans and fences, and the scanner that leaves fenced code alone."""

import re
from collections.abc import Callable

from clearmd.backend.services.conversion.markdown_out.marks import (
    BARE_MARKER,
    FENCE_LINE,
    opens_fence,
)


def fence_for(code: str) -> str:
    longest = max((len(run) for run in re.findall("`+", code)), default=0)
    return "`" * max(3, longest + 1)


def inline_code(code: str) -> str:
    # One line: a code span cannot cross a blank line (it would stay open and its content live),
    # and CommonMark shows its line breaks as spaces anyway.
    code = re.sub(r"[ \t]*\n\s*", " ", code)
    if "`" not in code:
        return f"`{code}`"
    ticks = "`" * (max(len(run) for run in re.findall("`+", code)) + 1)
    return f"{ticks} {code} {ticks}"


def outside_code(text: str, fix: Callable[[str], str], *, blank_around: bool = False) -> str:
    """``fix`` applied to the text between fenced code blocks; the blocks stay as they are.

    A line scanner (linear): a fence closes on a line of the same character, at least as long,
    with nothing else on it (CommonMark); an unclosed fence runs to the end.
    """
    pieces: list[tuple[bool, list[str]]] = [(False, [])]
    fence: str | None = None
    for line in text.split("\n"):
        found = FENCE_LINE.fullmatch(line)
        if fence is None and found is not None and opens_fence(found):
            fence = found.group(1)
            pieces.append((True, [line]))
        elif fence is not None:
            pieces[-1][1].append(line)
            run = found.group(1) if found is not None and not found.group(2).strip() else ""
            if run and run[0] == fence[0] and len(run) >= len(fence):
                fence = None
                pieces.append((False, []))
        else:
            pieces[-1][1].append(line)
    if not blank_around:
        return "\n".join(
            "\n".join(lines) if is_code else fix("\n".join(lines)) for is_code, lines in pieces
        )
    # Exactly one blank line between a code block and the text around it, except right after a
    # list marker alone on its line: the fence is that item's content (a blank line there would
    # leave the item empty and the code outside the list).
    parts = [
        "\n".join(lines) if is_code else fix("\n".join(lines)).strip("\n")
        for is_code, lines in pieces
    ]
    out: list[str] = []
    for part in (p for p in parts if p):
        if out:
            last_line = out[-1].rsplit("\n", 1)[-1]
            out.append("\n" if BARE_MARKER.fullmatch(last_line) else "\n\n")
        out.append(part)
    return "".join(out)
