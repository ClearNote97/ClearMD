"""A merged document's footnotes keep their own names (features 026, 039, 040)."""

import re

_FOOTNOTE = re.compile(r"\[\^([^\]\s]{1,64})\]")
_DEFINED = re.compile(r"^ {0,3}\[\^([^\]\s]{1,64})\]:", re.MULTILINE)
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def own_footnotes(text: str, index: int) -> str:
    """The document's footnotes get its own names (``[^1]`` → ``[^d2-1]``): only labels that have
    a definition, and never inside code, where ``[^a-z]`` is a pattern (audit v4, B1-07)."""
    defined = set(_DEFINED.findall(text))
    if not defined:
        return text

    def rename(found: re.Match[str]) -> str:
        label = found.group(1)
        return f"[^d{index}-{label}]" if label in defined else found.group(0)

    out: list[str] = []
    fence: str | None = None
    for line in text.split("\n"):
        opened = _FENCE.match(line)
        if fence is not None:
            if opened and opened.group(1)[0] == fence[0] and len(opened.group(1)) >= len(fence):
                fence = None
            out.append(line)
            continue
        if opened:
            fence = opened.group(1)
            out.append(line)
            continue
        pieces = line.split("`")  # even pieces are outside code spans
        out.append(
            "`".join(_FOOTNOTE.sub(rename, p) if i % 2 == 0 else p for i, p in enumerate(pieces))
        )
    return "\n".join(out)
