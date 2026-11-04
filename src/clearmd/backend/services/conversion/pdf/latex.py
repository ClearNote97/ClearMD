r"""A display equation rebuilt as LaTeX from where its pieces stand (feature 015, ADR-0036).

A PDF draws an equation as characters and lines: a fraction is a numerator above a short bar and a
denominator below it, a script is a smaller character raised or lowered, a sum's limits stand
above and below it, a tall bracket spans what it holds. Read back in that order, they make LaTeX:
``CEF_{o}^{t+1} = \frac{0e/0d}{0a/0b}``, shown as a formula by any viewer with math (VS Code,
GitHub, Obsidian) and copied as text.

Only what is understood is written: anything unexpected (a piece no rule places, a character that
cannot be read, a page of formulas) gives None, and the equation is written as before (its
picture, or its rows as text).

Pure: characters and bars in, a LaTeX string (or None) out.
"""

import bisect
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

MAX_GLYPHS = 600  # an equation's characters at most: more is a page of formulas, not one
MAX_BARS = 64  # an equation's drawn lines at most: more is a drawing, not a formula
MAX_DEPTH = 8  # fractions, brackets and scripts inside one another
MAX_ROWS = 12  # an equation's rows (a system of constraints) at most
AXIS_EMS = 0.25  # the math axis (where a fraction's bar stands) above the baseline
TEXT_SHARE = 0.1  # of an equation's pieces: a size this many have may be its text's
SCRIPT_SIZE = 0.85  # a character this much smaller than the text's is a script or a limit
SCRIPT_SHIFT = 0.1  # of the text's size: a script's middle this far above or below its base's
SCRIPT_GAP = 0.6  # of the text's size: a script starts at most this far right of its base
STACK_GAP = 0.6  # of the text's size: pieces of a numerator this close are one numerator
BAR_REACH = 0.9  # of the text's size: a numerator starts at most this far above its bar
BAR_SLACK = 0.3  # of the text's size: a numerator reaches this far past its bar's ends
ROW_EMS = 0.4  # of the text's size: pieces whose axes are this close are on one row
TALL = 1.5  # a bracket taller than this many times the text's size spans what it holds
SPACE = 0.18  # of the text's size: a gap this wide between pieces is written as a space
QUAD = 1.2  # of the text's size: a gap this wide is written as a quad
WORD_LETTERS = 4  # lowercase letters in a row, with a vowel: a word ("produce")
LABEL_GAP = 1.5  # of the text's size: an equation's number stands this far from the rest
SAME_HEIGHT = 0.6  # of the shorter: two brackets that overlap this much are a pair

_LABEL = re.compile(r"\((\d{1,3}[a-z]?)\)")
_OPENERS = {"(": ")", "[": "]", "{": "}", "⟨": "⟩", "|": "|", "‖": "‖", "⌊": "⌋", "⌈": "⌉"}
_CLOSERS = frozenset(_OPENERS.values())
_SYMMETRIC = frozenset({"|", "‖"})
_BIG_OPERATORS = {
    "∑": r"\sum", "∏": r"\prod", "∐": r"\coprod", "∫": r"\int", "∬": r"\iint", "∭": r"\iiint",
    "∮": r"\oint", "⋃": r"\bigcup", "⋂": r"\bigcap", "⨁": r"\bigoplus", "⨂": r"\bigotimes",
    "⋁": r"\bigvee", "⋀": r"\bigwedge",
}  # fmt: skip
_DELIMITERS = {"(": "(", ")": ")", "[": "[", "]": "]", "{": r"\{", "}": r"\}", "|": "|",
               "‖": r"\|", "⟨": r"\langle", "⟩": r"\rangle", "⌊": r"\lfloor", "⌋": r"\rfloor",
               "⌈": r"\lceil", "⌉": r"\rceil"}  # fmt: skip
_SYMBOLS = {
    "α": r"\alpha", "β": r"\beta", "γ": r"\gamma", "δ": r"\delta", "ε": r"\varepsilon",
    "ϵ": r"\epsilon", "ζ": r"\zeta", "η": r"\eta", "θ": r"\theta", "ϑ": r"\vartheta",
    "ι": r"\iota", "κ": r"\kappa", "λ": r"\lambda", "μ": r"\mu", "ν": r"\nu", "ξ": r"\xi",
    "π": r"\pi", "ϖ": r"\varpi", "ρ": r"\rho", "ϱ": r"\varrho", "σ": r"\sigma", "ς": r"\varsigma",
    "τ": r"\tau", "υ": r"\upsilon", "φ": r"\varphi", "ϕ": r"\phi", "χ": r"\chi", "ψ": r"\psi",
    "ω": r"\omega", "Γ": r"\Gamma", "Δ": r"\Delta", "Θ": r"\Theta", "Λ": r"\Lambda",
    "Ξ": r"\Xi", "Π": r"\Pi", "Σ": r"\Sigma", "Υ": r"\Upsilon", "Φ": r"\Phi", "Ψ": r"\Psi",
    "Ω": r"\Omega", "≤": r"\leq", "≥": r"\geq", "≦": r"\leqq", "≧": r"\geqq", "≠": r"\neq",
    "≈": r"\approx", "≡": r"\equiv", "∼": r"\sim", "≃": r"\simeq", "≅": r"\cong",
    "∝": r"\propto", "≪": r"\ll", "≫": r"\gg", "∈": r"\in", "∉": r"\notin", "∋": r"\ni",
    "⊂": r"\subset", "⊃": r"\supset", "⊆": r"\subseteq", "⊇": r"\supseteq", "∪": r"\cup",
    "∩": r"\cap", "∅": r"\emptyset", "∀": r"\forall", "∃": r"\exists", "¬": r"\neg",
    "∧": r"\wedge", "∨": r"\vee", "→": r"\to", "←": r"\leftarrow", "↔": r"\leftrightarrow",
    "⇒": r"\Rightarrow", "⇐": r"\Leftarrow", "⇔": r"\Leftrightarrow", "↦": r"\mapsto",
    "×": r"\times", "÷": r"\div", "·": r"\cdot", "⋅": r"\cdot", "∙": r"\cdot", "∗": "*",
    "±": r"\pm", "∓": r"\mp", "∘": r"\circ", "⊕": r"\oplus", "⊗": r"\otimes", "∞": r"\infty",
    "∂": r"\partial", "∇": r"\nabla", "√": r"\surd", "…": r"\ldots", "⋯": r"\cdots",
    "⋮": r"\vdots", "⋱": r"\ddots", "∕": "/", "⁄": "/", "−": "-",
    "–": "-", "ℝ": r"\mathbb{R}", "ℕ": r"\mathbb{N}", "ℤ": r"\mathbb{Z}", "ℚ": r"\mathbb{Q}",
    "ℂ": r"\mathbb{C}", "ℓ": r"\ell", "ℏ": r"\hbar", "∠": r"\angle",
    "⊥": r"\perp", "∥": r"\parallel", "∣": r"\mid", "⟂": r"\perp", "†": r"\dagger",
    "°": r"{}^{\circ}", "′": "{}'", "″": "{}''",
    "#": r"\#", "$": r"\$", "%": r"\%", "&": r"\&", "_": r"\_", "~": r"\sim",
    "\\": r"\backslash", " ": " ",
}  # fmt: skip
# An accent drawn over a letter (β̂, ȳ): its command, put on the piece below it.
_ACCENTS = {
    "ˆ": r"\hat", "^": r"\hat", "\u0302": r"\hat", "¯": r"\bar", "ˉ": r"\bar",
    "\u0304": r"\bar", "˜": r"\tilde", "\u0303": r"\tilde", "˙": r"\dot", "\u0307": r"\dot",
    "¨": r"\ddot", "\u0308": r"\ddot", "´": r"\acute", "`": r"\grave", "ˇ": r"\check",
    "\u20d7": r"\vec",
}  # fmt: skip
_INVISIBLE = frozenset({"Cc", "Cf", "Co", "Cs", "Cn", "Zl", "Zp", "Mn", "Me"})
_FUNCTIONS = frozenset(
    "sin cos tan cot sec csc arcsin arccos arctan sinh cosh tanh log ln lg exp det dim ker "
    "deg gcd hom arg max min sup inf lim liminf limsup Pr".split()
)
_OPERATOR_WORDS = frozenset("Max Min Sup Inf Lim argmax argmin Argmax Argmin".split())
_WORDS = frozenset(
    "if for and or otherwise where with such that si para donde con subject to sujeto can the "
    "all any are not has let set its per una los las del por que".split()
)
UNREADABLE = "�"


@dataclass(frozen=True)
class Glyph:
    """A character as drawn: its tight box, the size it is set in, and its baseline."""

    text: str
    left: float
    right: float
    bottom: float
    top: float
    size: float
    baseline: float


@dataclass(frozen=True)
class Bar:
    """A thin horizontal line drawn among the characters: a fraction's bar, an overline."""

    left: float
    right: float
    at: float


@dataclass
class _Node:
    latex: str
    left: float
    right: float
    bottom: float
    top: float
    size: float
    axis: float  # the height its row's axis passes at
    char: str = ""  # a single character's text ("" for a built piece)
    tall: bool = False  # a bracket spanning more than a line, or a sum
    scripts: dict[str, str] = field(default_factory=dict)  # "^", "_" (or limits: "over", "under")
    reach: float = -math.inf  # how far right its scripts go

    @property
    def middle(self) -> float:
        return (self.bottom + self.top) / 2

    @property
    def middle_x(self) -> float:
        return (self.left + self.right) / 2


class _Unsure(Exception):
    """A piece no rule places: the equation is not rewritten."""


def to_latex(glyphs: list[Glyph], bars: list[Bar]) -> str | None:
    """The equation as LaTeX (its number as ``\\tag``), or None when any of it is unsure."""
    if not glyphs or len(glyphs) > MAX_GLYPHS or len(bars) > MAX_BARS:
        return None
    if any(UNREADABLE in glyph.text for glyph in glyphs):
        return None
    glyphs, tag = _without_label(glyphs)
    if not glyphs:
        return None
    try:
        body = _layout([_node(glyph) for glyph in glyphs], list(bars), 0)
    except (_Unsure, ValueError, ZeroDivisionError, RecursionError):
        return None  # unsure is never a failure: the equation is written as before
    if not body.strip():
        return None
    latex = f"{body} \\tag{{{tag}}}" if tag else body
    return latex if _balanced(latex) else None


def _node(glyph: Glyph) -> _Node:
    if glyph.text in _ACCENTS:  # before NFKC, which turns "¯" into a space and a mark
        axis = glyph.baseline + AXIS_EMS * glyph.size
        box = (glyph.left, glyph.right, glyph.bottom, glyph.top)
        return _Node(_ACCENTS[glyph.text], *box, glyph.size, axis, char=glyph.text)
    char = unicodedata.normalize("NFKC", glyph.text) if len(glyph.text) == 1 else glyph.text
    if char in _BIG_OPERATORS or char in _OPENERS or char in _CLOSERS:
        axis = (glyph.bottom + glyph.top) / 2  # drawn around the axis, whatever its baseline
    else:
        axis = glyph.baseline + AXIS_EMS * glyph.size
    return _Node(
        _char_latex(char),
        glyph.left,
        glyph.right,
        glyph.bottom,
        glyph.top,
        glyph.size,
        axis,
        char=char,
    )


def _char_latex(char: str) -> str:
    if char in _BIG_OPERATORS:
        return _BIG_OPERATORS[char]
    if char in _DELIMITERS:
        return _DELIMITERS[char]
    if char in _SYMBOLS:
        return _SYMBOLS[char]
    if len(char) > 1:
        return "".join(_char_latex(part) for part in char)
    if unicodedata.category(char) in _INVISIBLE:
        raise _Unsure  # a control, a mark, a direction change: never in the formula unseen
    return char


def _without_label(glyphs: list[Glyph]) -> tuple[list[Glyph], str]:
    """The equation's number, "(7)" at its right, set apart: written as ``\\tag{7}``."""
    ordered = sorted(glyphs, key=lambda glyph: glyph.left)
    for count in range(3, 6):
        if count > len(ordered):
            break
        tail = ordered[-count:]
        found = _LABEL.fullmatch("".join(glyph.text for glyph in tail))
        if found is None:
            continue
        rest = ordered[:-count]
        size = max(glyph.size for glyph in tail)
        start = tail[0].left
        if not rest or max(glyph.right for glyph in rest) <= start - LABEL_GAP * size:
            return rest, found.group(1)
    return glyphs, ""


def _layout(nodes: list[_Node], bars: list[Bar], depth: int) -> str:
    """The pieces as LaTeX: fractions first (each bar's numerator and denominator), then tall
    brackets with what they hold, then the rows, each piece with its scripts."""
    if depth > MAX_DEPTH:
        raise _Unsure
    if not nodes:
        return ""
    nodes = _fractions(nodes, bars, depth)
    size = _text_size(nodes)
    nodes = _accents(nodes, size)
    nodes = _limits(nodes, size, depth)
    nodes = _brackets(nodes, size, depth)
    rows = _rows(nodes, size, depth)
    if len(rows) > MAX_ROWS:
        raise _Unsure
    if len(rows) == 1:
        return rows[0]
    # Each row in display style: its fractions and sums as large as on the page.
    return (
        r"\begin{array}{l} "
        + r" \\ ".join(rf"\displaystyle {row}" for row in rows)
        + r" \end{array}"
    )


def _text_size(nodes: list[_Node]) -> float:
    """The text's size: the largest one a fair share of the pieces have (an equation may hold
    more script than text: "(x^{t+1}, y^{t+1})"); never a sum's or a tall bracket's."""
    sizes = Counter(
        round(node.size, 1) for node in nodes
        if not node.tall and node.char not in _BIG_OPERATORS
        and node.char not in _OPENERS and node.char not in _CLOSERS
    )  # fmt: skip
    if not sizes:
        return max(node.size for node in nodes)
    total = sum(sizes.values())
    shared = [size for size, count in sizes.items() if count >= TEXT_SHARE * total]
    return max(shared, default=sizes.most_common(1)[0][0])


def _fractions(nodes: list[_Node], bars: list[Bar], depth: int) -> list[_Node]:
    """Each bar, widest first, with what stands right above and below it: a fraction, an
    overline (a root's, after "√"), an underline; a short bar alone on a row is a minus."""
    bars, nodes = _drawn_equals(bars, nodes)
    pending = sorted(bars, key=lambda bar: bar.left - bar.right)  # widest first
    while pending:
        bar = pending.pop(0)
        size = _near_size(nodes, bar)
        above = _stack(nodes, pending, bar, size, upwards=True)
        below = _stack(nodes, pending, bar, size, upwards=False)
        taken_nodes = {id(node) for node in above[0] + below[0]}
        taken_bars = {id(item) for item in above[1] + below[1]}
        if not above[0] and not below[0]:
            if bar.right - bar.left <= 1.2 * size and nodes:
                nodes = [*nodes, _Node("-", bar.left, bar.right, bar.at, bar.at, size, bar.at)]
            continue  # a rule the equation does not use
        pending = [item for item in pending if id(item) not in taken_bars]
        rest = [node for node in nodes if id(node) not in taken_nodes]
        if above[0] and below[0]:
            numerator = _layout(above[0], above[1], depth + 1)
            denominator = _layout(below[0], below[1], depth + 1)
            latex = rf"\frac{{{numerator}}}{{{denominator}}}"
            members = above[0] + below[0]
        elif below[0]:
            inner = _layout(below[0], below[1], depth + 1)
            root = _root(rest, bar, size)
            if root is not None:
                rest = [node for node in rest if node is not root]
                latex, members = rf"\sqrt{{{inner}}}", [*below[0], root]
            else:
                latex, members = rf"\overline{{{inner}}}", below[0]
        else:
            inner = _layout(above[0], above[1], depth + 1)
            latex, members = rf"\underline{{{inner}}}", above[0]
        built = _Node(
            latex,
            min(bar.left, *(node.left for node in members)),
            max(bar.right, *(node.right for node in members)),
            min(bar.at, *(node.bottom for node in members)),
            max(bar.at, *(node.top for node in members)),
            size,
            bar.at if above[0] and below[0] else _axis_of(members),
        )
        nodes = [*rest, built]
    return nodes


def _drawn_equals(bars: list[Bar], nodes: list[_Node]) -> tuple[list[Bar], list[_Node]]:
    """Two short bars of the same ends, one right over the other: an "=" drawn as lines."""
    left_over: list[Bar] = []
    used: set[int] = set()
    ordered = sorted(bars, key=lambda bar: bar.at)
    for index, bar in enumerate(ordered):
        if id(bar) in used:
            continue
        size = _near_size(nodes, bar)
        pair = next(
            (other for other in ordered[index + 1 :]
             if id(other) not in used and 0 < other.at - bar.at <= 0.5 * size
             and abs(other.left - bar.left) <= 0.5 and abs(other.right - bar.right) <= 0.5
             and other.right - other.left <= 1.5 * size),
            None,
        )  # fmt: skip
        if pair is None:
            left_over.append(bar)
            continue
        used.update((id(bar), id(pair)))
        middle = (bar.at + pair.at) / 2
        nodes = [*nodes, _Node("=", bar.left, bar.right, bar.at, pair.at, size, middle, char="=")]
    return left_over, nodes


def _accents(nodes: list[_Node], size: float) -> list[_Node]:
    """Each accent on the piece right below it (``\\hat{\\beta}``); one with nothing below it
    is unsure."""
    accents = [node for node in nodes if node.char in _ACCENTS]
    if not accents:
        return nodes
    for accent in accents:
        below = [
            node for node in nodes
            if node.char not in _ACCENTS
            and node.left - 0.25 * size <= accent.middle_x <= node.right + 0.25 * size
            and node.middle < accent.middle and node.top <= accent.bottom + 0.4 * size
        ]  # fmt: skip
        if not below:
            raise _Unsure
        base = max(below, key=lambda node: node.top)
        base.latex = f"{accent.latex}{{{base.latex}}}"
        base.char = ""  # no longer a plain letter of a word
    return [node for node in nodes if node.char not in _ACCENTS]


def _axis_of(members: list[_Node]) -> float:
    return Counter(round(node.axis, 1) for node in members).most_common(1)[0][0]


def _near_size(nodes: list[_Node], bar: Bar) -> float:
    """The size of the text around a bar (its numerator's, mostly)."""
    near = [
        node.size for node in nodes
        if node.right >= bar.left and node.left <= bar.right
        and abs(node.middle - bar.at) <= 3 * node.size
    ]  # fmt: skip
    return Counter(round(size, 1) for size in near).most_common(1)[0][0] if near else 10.0


def _stack(
    nodes: list[_Node], bars: list[Bar], bar: Bar, size: float, *, upwards: bool
) -> tuple[list[_Node], list[Bar]]:
    """What stands right above (or below) a bar, within its ends: pieces and bars one on another,
    each close to the one before it, from the bar outwards."""
    slack = BAR_SLACK * size

    def within(left: float, right: float) -> bool:
        middle = (left + right) / 2
        return (
            bar.left - slack <= left
            and right <= bar.right + slack
            and bar.left <= middle <= bar.right
        )

    sign = 1.0 if upwards else -1.0
    items: list[tuple[float, float, _Node | Bar]] = []  # (near edge, far edge) from the bar
    for node in nodes:
        near, far = (node.bottom, node.top) if upwards else (node.top, node.bottom)
        if within(node.left, node.right) and sign * (node.middle - bar.at) > 0:
            items.append((sign * (near - bar.at), sign * (far - bar.at), node))
    for other in bars:
        if within(other.left, other.right) and sign * (other.at - bar.at) > 0:
            items.append((sign * (other.at - bar.at), sign * (other.at - bar.at), other))
    items.sort(key=lambda item: item[0])
    # The rows beside the bar: full-size pieces outside its ends (and outside any other bar's).
    beside = sorted(
        node.axis for node in nodes
        if not within(node.left, node.right) and node.size >= SCRIPT_SIZE * size
        and not any(other.left <= node.middle_x <= other.right for other in bars)
    )  # fmt: skip
    reach = BAR_REACH * size
    taken_nodes: list[_Node] = []
    taken_bars: list[Bar] = []
    for near, far, item in items:
        if near > reach:
            break
        if isinstance(item, _Node) and taken_nodes and _on_a_row(item.axis, beside, size):
            break  # the row above (or below) the fraction's, not its numerator
        if isinstance(item, Bar):
            taken_bars.append(item)
        else:
            taken_nodes.append(item)
        reach = max(reach, far + STACK_GAP * size)
    return taken_nodes, taken_bars


def _on_a_row(axis: float, rows: list[float], size: float) -> bool:
    at = bisect.bisect_left(rows, axis - ROW_EMS * size)
    return at < len(rows) and rows[at] <= axis + ROW_EMS * size


def _root(nodes: list[_Node], bar: Bar, size: float) -> _Node | None:
    """The "√" whose bar this is: right before its start, as high."""
    return next(
        (node for node in nodes
         if node.char == "√" and abs(node.right - bar.left) <= 0.6 * size
         and node.top >= bar.at - 0.4 * size),
        None,
    )  # fmt: skip


def _limits(nodes: list[_Node], size: float, depth: int) -> list[_Node]:
    """A sum's limits: the smaller pieces right above and below it, within its width."""
    operators = [node for node in nodes if node.char in _BIG_OPERATORS]
    if not operators:
        return nodes
    taken: set[int] = set()
    for operator in operators:
        operator.tall = True
        reach = max(operator.right - operator.left, size)
        for place, upwards in (("over", True), ("under", False)):
            found = [
                node for node in nodes
                if id(node) not in taken and node is not operator
                and node.size < SCRIPT_SIZE * size
                and abs((node.left + node.right) / 2 - (operator.left + operator.right) / 2)
                <= reach
                and (node.bottom >= operator.top - 0.25 * size if upwards
                     else node.top <= operator.bottom + 0.25 * size)
                and (node.bottom - operator.top if upwards else operator.bottom - node.top)
                <= 1.2 * size
            ]  # fmt: skip
            found = _row_of(found, operator, upwards)
            if found:
                operator.scripts[place] = _layout(found, [], depth + 1)
                taken.update(id(node) for node in found)
    return [node for node in nodes if id(node) not in taken]


def _row_of(found: list[_Node], operator: _Node, upwards: bool) -> list[_Node]:
    """The row of limits next to the operator (the nearest one), all of it."""
    if not found:
        return []
    nearest = min(found, key=lambda node: abs(node.middle - operator.middle))
    return [node for node in found if abs(node.axis - nearest.axis) <= 0.5 * nearest.size]


def _brackets(nodes: list[_Node], size: float, depth: int) -> list[_Node]:
    """Tall brackets with what they hold: ``\\left[ … \\right]``, innermost first. Bars
    ("|…|", "‖…‖") pair from the left with the next one alike; a tall brace with no closing one
    holds the rest of its height (a system: ``\\left\\{ … \\right.``)."""
    for node in nodes:
        if node.char in _OPENERS or node.char in _CLOSERS:
            node.tall = node.top - node.bottom > TALL * size
    bars = sorted((n for n in nodes if n.tall and n.char in _SYMMETRIC), key=lambda n: n.left)
    while bars:
        opener = bars.pop(0)
        closer = next((n for n in bars if n.char == opener.char and _level(opener, n)), None)
        if closer is None:
            opener.tall = False
            continue
        bars.remove(closer)
        nodes = _enclosed(nodes, opener, closer, size, depth)
    openers = sorted(
        (node for node in nodes if node.tall and node.char in _OPENERS),
        key=lambda node: -node.left,
    )
    for opener in openers:
        if opener not in nodes:
            continue
        closer = next(
            (node for node in sorted(nodes, key=lambda n: n.left)
             if node is not opener and node.tall and node.char in _CLOSERS
             and node.char not in _SYMMETRIC
             and node.left >= opener.right - 0.1 * size and _level(opener, node)),
            None,
        )  # fmt: skip
        if closer is None and opener.char != "{":
            opener.tall = False  # an unmatched one is written as a plain bracket
            continue
        nodes = _enclosed(nodes, opener, closer, size, depth)
    for node in nodes:
        if node.char in _CLOSERS and node.tall:
            node.tall = False  # a closing one with no opening one: plain
    return nodes


def _enclosed(
    nodes: list[_Node], opener: _Node, closer: _Node | None, size: float, depth: int
) -> list[_Node]:
    """The pieces between two tall brackets (or after a brace), as one piece."""
    end = closer.left if closer is not None else max(node.right for node in nodes)
    inside = [
        node for node in nodes
        if node is not opener and node is not closer
        and node.left >= opener.right - 0.2 * size and node.right <= end + 0.2 * size
        and opener.bottom - 0.2 * size <= node.axis <= opener.top + 0.2 * size
    ]  # fmt: skip
    inner = _layout(inside, [], depth + 1) if inside else ""
    right = rf"\right{_DELIMITERS[closer.char]}" if closer is not None else r"\right."
    members = [opener, *inside, *([closer] if closer is not None else [])]
    built = _Node(
        rf"\left{_DELIMITERS[opener.char]} {inner} {right}",
        opener.left,
        max(node.right for node in members),
        min(node.bottom for node in members),
        max(node.top for node in members),
        size,
        opener.middle,
        tall=True,
    )
    gone = {id(node) for node in members}
    return [*(node for node in nodes if id(node) not in gone), built]


def _level(opener: _Node, closer: _Node) -> bool:
    overlap = min(opener.top, closer.top) - max(opener.bottom, closer.bottom)
    shorter = min(opener.top - opener.bottom, closer.top - closer.bottom)
    return shorter > 0 and overlap >= SAME_HEIGHT * shorter


def _rows(nodes: list[_Node], size: float, depth: int) -> list[str]:
    """The pieces in rows (by their axis), each row from the left, scripts on their bases."""
    bases = [node for node in nodes if node.size >= SCRIPT_SIZE * size or node.tall]
    small = sorted(
        (node for node in nodes if not (node.size >= SCRIPT_SIZE * size or node.tall)),
        key=lambda node: node.left,
    )
    loose: list[_Node] = []
    runs: list[tuple[_Node, str, list[_Node]]] = []  # base, kind, pieces
    for node in small:
        run = next(
            (run for run in reversed(runs)
             if node.left - run[2][-1].right <= 0.35 * size
             and node.left >= run[2][-1].left
             and abs(node.axis - run[2][-1].axis) <= 0.35 * node.size),
            None,
        )  # fmt: skip
        if run is not None:
            run[2].append(node)
            continue
        attached = _base_of(node, bases, size)
        if attached is None:
            loose.append(node)
        else:
            runs.append((attached[0], attached[1], [node]))
    for base, kind, pieces in runs:
        base.reach = max(base.reach, *(piece.right for piece in pieces))
        latex = _layout(pieces, [], depth + 1)
        if kind in base.scripts:  # two runs of one kind on a base: written one after the other
            base.scripts[kind] += " " + latex
        else:
            base.scripts[kind] = latex
    placed = bases + loose
    if not placed:
        return []
    rows: list[list[_Node]] = []
    for node in sorted(placed, key=lambda node: -node.axis):
        if rows and abs(rows[-1][0].axis - node.axis) <= ROW_EMS * size:
            rows[-1].append(node)
        else:
            rows.append([node])
    return [_row_text(sorted(row, key=lambda node: node.left), size) for row in rows]


def _base_of(node: _Node, bases: list[_Node], size: float) -> tuple[_Node, str] | None:
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


def _row_text(row: list[_Node], size: float) -> str:
    """A row's pieces, joined: words as words ("Max", "if"), a space where there was one."""
    out: list[str] = []
    index = 0
    previous: _Node | None = None
    while index < len(row):
        end = index
        while (
            end + 1 < len(row)
            and _letter(row[end]) and _letter(row[end + 1])
            and not ({"^", "_"} & row[end].scripts.keys())
            and row[end + 1].left - row[end].right <= SPACE * size
        ):  # fmt: skip
            end += 1
        word = "".join(node.char for node in row[index : end + 1])
        last = row[end]
        prose = word in _WORDS or _a_word(word)
        if end > index and (word in _FUNCTIONS or word in _OPERATOR_WORDS or prose):
            limits: dict[str, str] = {}
            for node in row[index : end + 1]:
                for kind, latex in node.scripts.items():
                    limits[kind] = f"{limits[kind]} {latex}" if kind in limits else latex
            if word in _FUNCTIONS:
                piece = "\\" + word
            elif word in _OPERATOR_WORDS:
                piece = rf"\operatorname*{{{word}}}"
            else:
                piece = rf"\text{{ {word} }}"
            piece = _with_scripts(piece, limits, operator=not prose)
        else:
            end = index
            node = row[index]
            piece = _with_scripts(node.latex, node.scripts, operator=node.char in _BIG_OPERATORS)
            last = node
        first = row[index]
        if previous is not None:
            gap = first.left - max(previous.right, previous.reach)
            if gap > QUAD * size:
                out.append(r" \quad ")  # set apart on the page: "x_{n} \quad n = 1, …"
            else:
                out.append(" " if gap > SPACE * size or _glued(out[-1], piece) else "")
        out.append(piece)
        previous = last
        index = end + 1
    return "".join(out)


def _a_word(word: str) -> bool:
    """A word of the text inside the equation ("x can produce y"): four lowercase letters or
    more, with a vowel ("abc", "ijk" are products of variables)."""
    return len(word) >= WORD_LETTERS and word.islower() and any(c in "aeiou" for c in word)


def _letter(node: _Node) -> bool:
    return len(node.char) == 1 and node.char.isalpha() and node.char.isascii()


def _glued(before: str, after: str) -> bool:
    """A command followed by a letter needs a space between them (``\\theta y``)."""
    return re.search(r"\\[A-Za-z]+$", before) is not None and after[:1].isalpha()


def _with_scripts(latex: str, scripts: dict[str, str], *, operator: bool) -> str:
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


def _balanced(latex: str) -> bool:
    """Braces, ``\\left``/``\\right`` and ``\\begin``/``\\end`` in pairs (a check of the
    writer: never a formula a viewer would refuse)."""
    depth = 0
    escaped = False
    for char in latex:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                return False
    if depth:
        return False
    lefts = len(re.findall(r"\\left(?![a-z])", latex))
    rights = len(re.findall(r"\\right(?![a-z])", latex))
    return lefts == rights and latex.count(r"\begin{") == latex.count(r"\end{")
