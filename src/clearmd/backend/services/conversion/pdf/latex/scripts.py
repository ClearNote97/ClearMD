"""Where a small piece is set on a base, and how a piece writes its scripts (015)."""

from clearmd.backend.services.conversion.pdf.latex.nodes import Node

SCRIPT_GAP = 0.6  # of the text's size: a script starts at most this far right of its base
SCRIPT_SHIFT = 0.1  # of the text's size: a script's middle this far above or below its base's


def base_of(node: Node, bases: list[Node], size: float) -> tuple[Node, str] | None:
    """The piece a small one is set on, and how: raised ("^"), lowered ("_"), or a limit right
    under or over a word ("Max" with "z,θ" under it)."""
    for base in bases:  # right under or over a piece, within its width ("Max" with "z,θ")
        if not base.left <= node.middle_x <= base.right:
            continue
        if base.bottom - 1.0 * size <= node.top <= base.bottom + 0.15 * size:
            return base, "under"
        if base.top - 0.15 * size <= node.bottom <= base.top + 1.0 * size:
            return base, "over"
    candidates = [
        base for base in bases
        if base.right <= node.left + 0.35 * size
        and node.left - base.right <= SCRIPT_GAP * size
        and base.bottom - 0.6 * size <= node.middle <= base.top + 0.6 * size
    ]  # fmt: skip
    if candidates:
        base = max(candidates, key=lambda base: base.right)
        if node.axis > base.axis + SCRIPT_SHIFT * size:
            return base, "^"
        if node.axis < base.axis - SCRIPT_SHIFT * size:
            return base, "_"
        return None
    return None


def with_scripts(latex: str, scripts: dict[str, str], *, operator: bool) -> str:
    """A piece and its scripts. An operator's limits go under and over it (``\\sum_{j=1}^{J}``,
    ``\\operatorname*{Max}_{z}``); another piece's with ``\\underset`` and ``\\overset``."""
    under, over = scripts.get("under", ""), scripts.get("over", "")
    lowered, raised = scripts.get("_", ""), scripts.get("^", "")
    if operator:
        lowered = " ".join(part for part in (under, lowered) if part)
        raised = " ".join(part for part in (over, raised) if part)
    else:
        if under:
            latex = rf"\underset{{{under}}}{{{latex}}}"
        if over:
            latex = rf"\overset{{{over}}}{{{latex}}}"
    if lowered:
        latex += f"_{{{lowered}}}"
    if raised:
        latex += f"^{{{raised}}}"
    return latex
