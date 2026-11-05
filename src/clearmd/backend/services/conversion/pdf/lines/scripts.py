"""A line's text with its scripts written as such, in Unicode or as ^{...} and _{...} (014)."""

from clearmd.backend.services.conversion.pdf.lines.script_marks import script_marks
from clearmd.backend.services.conversion.pdf.model import Chars

# The letters Unicode has as scripts: a script made only of them is written with them (014).
_SUPERSCRIPTS = dict(
    zip(
        "0123456789+-−=()abcdefghijklmnoprstuvwxyzABDEGHIJKLMNOPRTUVW′″θ*",
        "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻⁼⁽⁾ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻᴬᴮᴰᴱᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾᴿᵀᵁⱽᵂ′″ᶿ*",
        strict=True,
    )
)
_SUBSCRIPTS = dict(
    zip("0123456789+-−=()aehijklmnoprstuvx", "₀₁₂₃₄₅₆₇₈₉₊₋₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ", strict=True)
)
HUG_EMS = 0.12  # a space narrower than this (a word's is about a quarter) touches a script


def scripted(pieces: list[tuple[str, int]], chars: Chars, visible: list[int]) -> str:
    """The line's text, its sub- and superscripts written as such (014): a character smaller than
    the line's text, its baseline raised or lowered, as "EFᵗₒ", "Rᴺ₊", "zⱼ", a footnote's "²";
    a script with no such letter in Unicode as "^{…}" or "_{…}". The space PDFium puts around a
    script that touches its base goes."""
    marks = script_marks(chars, visible)
    if not marks:
        return "".join(piece for piece, _ in pieces)
    # Each piece's nearest drawn character before and after it: one pass each way (linear,
    # however many spaces a line holds; review of 014).
    before, after = [-1] * len(pieces), [-1] * len(pieces)
    last = -1
    for position, (_, index) in enumerate(pieces):
        before[position] = last
        if index >= 0:
            last = index
    last = -1
    for position in range(len(pieces) - 1, -1, -1):
        after[position] = last
        if pieces[position][1] >= 0:
            last = pieces[position][1]
    kept: list[tuple[str, int, str]] = []
    for position, (piece, index) in enumerate(pieces):
        if piece == " " and hugs(before[position], after[position], marks, chars):
            continue
        kept.append((piece, index, marks.get(index, "")))
    out: list[str] = []
    run: list[str] = []
    mode = ""
    for piece, _, mark in [*kept, ("", -1, "")]:
        if mark != mode and run:
            out.append(script_text(run, mode))
            run = []
        mode = mark
        if mark:
            run.append(piece)
        else:
            out.append(piece)
    return "".join(out)


def hugs(before: int, after: int, marks: dict[int, str], chars: Chars) -> bool:
    """A space between a script and what it is set on, narrower than a real one."""
    if before < 0 or after < 0 or not (before in marks or after in marks):
        return False
    gap = chars.lefts[after] - chars.rights[before]
    return gap < HUG_EMS * max(chars.font_sizes[before], chars.font_sizes[after], 1.0)


def script_text(run: list[str], mode: str) -> str:
    table = _SUPERSCRIPTS if mode == "^" else _SUBSCRIPTS
    text = "".join(run)
    if all(char in table for char in text):
        return "".join(table[char] for char in text)
    return f"{mode}{{{text}}}"
