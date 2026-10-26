r"""LibreOffice Math formulas: a subset of presentation MathML → LaTeX (ADR-0024, spec 003).

Fractions, roots, scripts, big operators with limits, accents, fences, matrices, text, Greek
letters and the usual operators and relations. Anything else raises ``Unsupported`` and the whole
formula falls back to its StarMath source: never half a formula. The depth is bounded.
"""

import re

from clearmd.backend.services.conversion.odt.xmltree import Element

MAX_DEPTH = 64
STARMATH = "StarMath 5.0"

GREEK = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "varepsilon", "ϵ": "epsilon",
    "ζ": "zeta", "η": "eta", "θ": "theta", "ϑ": "vartheta", "ι": "iota", "κ": "kappa",
    "λ": "lambda", "μ": "mu", "ν": "nu", "ξ": "xi", "π": "pi", "ϖ": "varpi", "ρ": "rho",
    "ϱ": "varrho", "σ": "sigma", "ς": "varsigma", "τ": "tau", "υ": "upsilon", "φ": "varphi",
    "ϕ": "phi", "χ": "chi", "ψ": "psi", "ω": "omega", "Γ": "Gamma", "Δ": "Delta",
    "Θ": "Theta", "Λ": "Lambda", "Ξ": "Xi", "Π": "Pi", "Σ": "Sigma", "Υ": "Upsilon",
    "Φ": "Phi", "Ψ": "Psi", "Ω": "Omega",
}  # fmt: skip
SYMBOLS = {
    "∑": "\\sum", "∏": "\\prod", "∐": "\\coprod", "∫": "\\int", "∬": "\\iint", "∭": "\\iiint",
    "∮": "\\oint", "⋃": "\\bigcup", "⋂": "\\bigcap", "±": "\\pm", "∓": "\\mp", "×": "\\times",
    "·": "\\cdot", "⋅": "\\cdot", "∗": "\\ast", "÷": "\\div", "∘": "\\circ", "−": "-",
    "≤": "\\le", "≥": "\\ge", "≠": "\\neq", "≈": "\\approx", "≡": "\\equiv", "∼": "\\sim",
    "≃": "\\simeq", "≅": "\\cong", "∝": "\\propto", "≪": "\\ll", "≫": "\\gg", "→": "\\to",
    "←": "\\leftarrow", "↔": "\\leftrightarrow", "⇒": "\\Rightarrow", "⇐": "\\Leftarrow",
    "⇔": "\\Leftrightarrow", "↦": "\\mapsto", "∞": "\\infty", "∈": "\\in", "∉": "\\notin",
    "∋": "\\ni", "⊂": "\\subset", "⊃": "\\supset", "⊆": "\\subseteq", "⊇": "\\supseteq",
    "∪": "\\cup", "∩": "\\cap", "∅": "\\emptyset", "∀": "\\forall", "∃": "\\exists",
    "∄": "\\nexists", "¬": "\\neg", "∧": "\\wedge", "∨": "\\vee", "∂": "\\partial",
    "∇": "\\nabla", "′": "'", "″": "''", "…": "\\ldots", "⋯": "\\cdots", "⋮": "\\vdots",
    "⋱": "\\ddots", "⟨": "\\langle", "⟩": "\\rangle", "〈": "\\langle", "〉": "\\rangle",
    "‖": "\\|", "ℝ": "\\mathbb{R}", "ℕ": "\\mathbb{N}", "ℤ": "\\mathbb{Z}", "ℚ": "\\mathbb{Q}",
    "ℂ": "\\mathbb{C}", "ℏ": "\\hbar", "ℓ": "\\ell", "°": "^{\\circ}", "⊥": "\\perp",
    "∥": "\\parallel", "∠": "\\angle", "△": "\\triangle", "⊕": "\\oplus", "⊗": "\\otimes",
}  # fmt: skip
FUNCTIONS = frozenset(
    {
        "sin", "cos", "tan", "cot", "sec", "csc", "arcsin", "arccos", "arctan", "sinh", "cosh",
        "tanh", "coth", "log", "ln", "lg", "exp", "lim", "liminf", "limsup", "max", "min", "sup",
        "inf", "det", "dim", "ker", "deg", "gcd", "arg", "hom", "Pr",
    }
)  # fmt: skip
# LibreOffice writes these as one identifier or operator with a space or as a word.
WORDS = {"lim inf": "\\liminf", "lim sup": "\\limsup", "mod": "\\bmod"}
# ASCII characters LaTeX gives a meaning; written as text in math they need a backslash.
_LATEX_SPECIAL = {"{": "\\{", "}": "\\}", "#": "\\#", "%": "\\%", "&": "\\&", "$": "\\$",
                  "_": "\\_", "\\": "\\backslash", "~": "\\sim", "^": "\\hat{}"}  # fmt: skip
_TEXT_SPECIAL = {"{": "\\{", "}": "\\}", "#": "\\#", "%": "\\%", "&": "\\&", "$": "\\$",
                 "_": "\\_", "\\": "\\textbackslash{}", "~": "\\textasciitilde{}",
                 "^": "\\textasciicircum{}"}  # fmt: skip
ACCENTS = {
    "^": "\\hat", "ˆ": "\\hat", "̂": "\\hat", "¯": "\\overline", "‾": "\\overline",
    "→": "\\vec", "⃗": "\\vec", "~": "\\tilde", "˜": "\\tilde", "̃": "\\tilde", "˙": "\\dot",
    "¨": "\\ddot", "ˇ": "\\check", "˘": "\\breve", "´": "\\acute", "`": "\\grave",
    "˚": "\\mathring", "⃛": "\\dddot",
}  # fmt: skip
# Stretchy accents over more than one symbol (LibreOffice's widehat, widetilde, widevec).
WIDE_ACCENTS = {"^": "\\widehat", "ˆ": "\\widehat", "~": "\\widetilde", "˜": "\\widetilde",
                "→": "\\overrightarrow", "⃗": "\\overrightarrow"}  # fmt: skip
UNDER_ACCENTS = {"_": "\\underline", "¯": "\\underline", "‾": "\\underline", "̲": "\\underline"}
# mathvariant of an mstyle around its content.
VARIANTS = {"bold": "\\boldsymbol", "normal": "\\mathrm", "sans-serif": "\\mathsf",
            "bold-sans-serif": "\\mathsf", "monospace": "\\mathtt"}  # fmt: skip
FENCES = {"(": "(", ")": ")", "[": "[", "]": "]", "{": "\\{", "}": "\\}", "|": "|",
          "‖": "\\|", "⟨": "\\langle", "⟩": "\\rangle", "〈": "\\langle", "〉": "\\rangle",
          "⌊": "\\lfloor", "⌋": "\\rfloor", "⌈": "\\lceil", "⌉": "\\rceil"}  # fmt: skip
_CONTROL_WORD_END = re.compile(r"\\[A-Za-z]+$")


class Unsupported(Exception):
    """A MathML construct outside ClearMD's subset: the formula keeps its StarMath source."""


def _char(char: str, table: dict[str, str]) -> str:
    if char in GREEK:
        return f"\\{GREEK[char]}"
    if char in SYMBOLS:
        return SYMBOLS[char]
    return table.get(char, char)


def _text(element: Element) -> str:
    return " ".join(element.text().split())


def _join(parts: list[str]) -> str:
    """Pieces of LaTeX in order; a control word never glues to the letter after it. Linear:
    only the end of the previous piece is looked at."""
    out: list[str] = []
    for part in parts:
        if not part:
            continue
        if out and part[0].isalpha() and _CONTROL_WORD_END.search(out[-1][-64:]):
            out.append(" ")
        out.append(part)
    return "".join(out)


def _group(latex: str) -> str:
    return f"{{{latex}}}"


def _children(element: Element) -> list[Element]:
    return list(element.elements())


def _identifier(element: Element) -> str:
    text = _text(element)
    variant = element.get("mathvariant")
    if text in WORDS:
        return WORDS[text]
    if text in FUNCTIONS:
        return f"\\{text}"
    if len(text) == 1:
        letter = _char(text, _LATEX_SPECIAL)
    else:
        letter = "".join(_char(c, _LATEX_SPECIAL) for c in text)
    if variant == "bold":
        return f"\\mathbf{{{letter}}}"
    if variant == "normal" and len(text) > 1 and text.isalpha():
        return f"\\mathrm{{{letter}}}"
    return letter


def _operator(element: Element) -> str:
    text = _text(element)
    if text in WORDS:
        return WORDS[text]
    return "".join(_char(c, _LATEX_SPECIAL) for c in text)


def _fence_char(element: Element) -> str | None:
    if element.tag != "math:mo" or element.get("fence") != "true":
        return None
    if element.get("stretchy") == "false":
        return None
    return FENCES.get(_text(element))


def _rows(table: Element, depth: int) -> str:
    rows = []
    for row in table.elements():
        if row.tag != "math:mtr":
            raise Unsupported(row.tag)
        cells = []
        for cell in row.elements():
            if cell.tag != "math:mtd":
                raise Unsupported(cell.tag)
            cells.append(_row(_children(cell), depth + 1))
        rows.append(" & ".join(cells))
    return "\\begin{matrix}" + " \\\\ ".join(rows) + "\\end{matrix}"


def _row(elements: list[Element], depth: int) -> str:
    """A sequence; stretchy fences around it become \\left … \\right."""
    if len(elements) >= 2:
        opening, closing = _fence_char(elements[0]), _fence_char(elements[-1])
        if opening is not None and closing is not None:
            inner = _row(elements[1:-1], depth + 1)
            return _join([f"\\left{opening}", inner, f"\\right{closing}"])
        if opening is not None and elements[0].get("form") != "postfix":
            # "left lbrace … right none" (piecewise definitions): an invisible right fence.
            return _join([f"\\left{opening}", _row(elements[1:], depth + 1), "\\right."])
    return _join([_latex(element, depth + 1) for element in elements])


def _script(base: str, under: str | None, over: str | None) -> str:
    out = base
    if under is not None:
        out += f"_{_group(under)}"
    if over is not None:
        out += f"^{_group(over)}"
    return out


def _base(element: Element, depth: int) -> str:
    latex = _latex(element, depth + 1)
    simple = element.tag in {"math:mi", "math:mn", "math:mo"} and len(_text(element)) == 1
    return latex if simple or _CONTROL_WORD_END.fullmatch(latex) else _group(latex)


def _latex(element: Element, depth: int) -> str:
    if depth > MAX_DEPTH:
        raise Unsupported("nested too deeply")
    tag = element.tag
    kids = _children(element)
    if tag == "math:mstyle" and element.get("mathvariant") not in {"", "italic"}:
        command = VARIANTS.get(element.get("mathvariant"))
        if command is None:
            raise Unsupported(f"mstyle mathvariant={element.get('mathvariant')}")
        return f"{command}{_group(_row(kids, depth))}"
    if tag in {"math:mrow", "math:mstyle", "math:mpadded", "math:math"}:
        return _row(kids, depth)
    if tag == "math:semantics":
        presentation = [k for k in kids if k.tag not in {"math:annotation", "math:annotation-xml"}]
        return _row(presentation[:1], depth)
    if tag == "math:mi":
        return _identifier(element)
    if tag == "math:mn":
        return "".join(_LATEX_SPECIAL.get(c, c) for c in _text(element))
    if tag == "math:mo":
        return _operator(element)
    if tag == "math:mtext":
        text = "".join(_TEXT_SPECIAL.get(c, c) for c in element.text())
        return f"\\text{{{text}}}"
    if tag == "math:mspace":
        return "\\,"
    if len(kids) == 2 and tag == "math:mfrac":
        top, bottom = (_latex(k, depth + 1) for k in kids)
        if element.get("linethickness") in {"0", "0pt", "0px", "0em"}:
            return f"\\genfrac{{}}{{}}{{0pt}}{{}}{_group(top)}{_group(bottom)}"
        return f"\\frac{_group(top)}{_group(bottom)}"
    if tag == "math:msqrt":
        return f"\\sqrt{_group(_row(kids, depth))}"
    if tag == "math:mroot" and len(kids) == 2:
        index = _group(_latex(kids[1], depth + 1))  # braced: an index holding "]" stays one
        return f"\\sqrt[{index}]{_group(_latex(kids[0], depth + 1))}"
    if tag in {"math:msup", "math:msub", "math:msubsup"}:
        expected = 3 if tag == "math:msubsup" else 2
        if len(kids) != expected:
            raise Unsupported(tag)
        base = _base(kids[0], depth)
        rest = [_latex(k, depth + 1) for k in kids[1:]]
        if tag == "math:msup":
            return _script(base, None, rest[0])
        if tag == "math:msub":
            return _script(base, rest[0], None)
        return _script(base, rest[0], rest[1])
    if tag in {"math:munder", "math:mover", "math:munderover"}:
        return _under_over(element, kids, depth)
    if tag == "math:mfenced":
        opening = FENCES.get(element.get("open", "("), element.get("open", "("))
        closing = FENCES.get(element.get("close", ")"), element.get("close", ")"))
        separator = (element.get("separators", ",").strip() or ",")[0]
        inner = separator.join(_latex(k, depth + 1) for k in kids)
        return _join([f"\\left{opening or '.'}", inner, f"\\right{closing or '.'}"])
    if tag == "math:mtable":
        return _rows(element, depth)
    raise Unsupported(tag)


def _under_over(element: Element, kids: list[Element], depth: int) -> str:
    tag = element.tag
    expected = 3 if tag == "math:munderover" else 2
    if len(kids) != expected:
        raise Unsupported(tag)
    base_element = kids[0]
    base_text = _text(base_element)
    big = base_element.tag in {"math:mo", "math:mi"} and (
        base_text in SYMBOLS or base_text in FUNCTIONS or base_text in WORDS
    )
    if tag == "math:mover" and not big:
        mark = _text(kids[1])
        wide = kids[1].get("stretchy") == "true" and len(_text(base_element)) > 1
        if kids[1].tag == "math:mo" and wide and mark in WIDE_ACCENTS:
            return f"{WIDE_ACCENTS[mark]}{_group(_latex(base_element, depth + 1))}"
        if kids[1].tag == "math:mo" and mark in ACCENTS:
            return f"{ACCENTS[mark]}{_group(_latex(base_element, depth + 1))}"
        above = _group(_latex(kids[1], depth + 1))
        return f"\\overset{above}{_group(_latex(base_element, depth + 1))}"
    if tag == "math:munder" and not big:
        mark = _text(kids[1])
        if kids[1].tag == "math:mo" and mark in UNDER_ACCENTS:
            return f"{UNDER_ACCENTS[mark]}{_group(_latex(base_element, depth + 1))}"
        below = _group(_latex(kids[1], depth + 1))
        return f"\\underset{below}{_group(_latex(base_element, depth + 1))}"
    base = _latex(base_element, depth + 1)
    under = _latex(kids[1], depth + 1) if tag != "math:mover" else None
    over = _latex(kids[-1], depth + 1) if tag != "math:munder" else None
    return _script(base, under, over)


def to_latex(math: Element) -> str:
    """The LaTeX of a ``math:math`` element; ``Unsupported`` outside the subset."""
    if math.tag != "math:math":
        raise Unsupported(math.tag)
    return _row(_children(math), 0)


def starmath(math: Element) -> str | None:
    """The StarMath source LibreOffice keeps next to the MathML, when there is one."""
    for element in math.walk():
        if element.tag == "math:annotation" and element.get("encoding") == STARMATH:
            source = " ".join(element.text().split())
            return source or None
    return None
