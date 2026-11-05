"""The tables of LaTeX: brackets, operators, Greek and math symbols, accents (feature 015)."""

import unicodedata

from clearmd.backend.services.conversion.pdf.latex.unsure import Unsure

OPENERS = {"(": ")", "[": "]", "{": "}", "⟨": "⟩", "|": "|", "‖": "‖", "⌊": "⌋", "⌈": "⌉"}
CLOSERS = frozenset(OPENERS.values())
SYMMETRIC = frozenset({"|", "‖"})
BIG_OPERATORS = {
    "∑": r"\sum", "∏": r"\prod", "∐": r"\coprod", "∫": r"\int", "∬": r"\iint", "∭": r"\iiint",
    "∮": r"\oint", "⋃": r"\bigcup", "⋂": r"\bigcap", "⨁": r"\bigoplus", "⨂": r"\bigotimes",
    "⋁": r"\bigvee", "⋀": r"\bigwedge",
}  # fmt: skip
DELIMITERS = {"(": "(", ")": ")", "[": "[", "]": "]", "{": r"\{", "}": r"\}", "|": "|",
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
ACCENTS = {
    "ˆ": r"\hat", "^": r"\hat", "\u0302": r"\hat", "¯": r"\bar", "ˉ": r"\bar",
    "\u0304": r"\bar", "˜": r"\tilde", "\u0303": r"\tilde", "˙": r"\dot", "\u0307": r"\dot",
    "¨": r"\ddot", "\u0308": r"\ddot", "´": r"\acute", "`": r"\grave", "ˇ": r"\check",
    "\u20d7": r"\vec",
}  # fmt: skip
_INVISIBLE = frozenset({"Cc", "Cf", "Co", "Cs", "Cn", "Zl", "Zp", "Mn", "Me"})


def char_latex(char: str) -> str:
    if char in BIG_OPERATORS:
        return BIG_OPERATORS[char]
    if char in DELIMITERS:
        return DELIMITERS[char]
    if char in _SYMBOLS:
        return _SYMBOLS[char]
    if len(char) > 1:
        return "".join(char_latex(part) for part in char)
    if unicodedata.category(char) in _INVISIBLE:
        raise Unsure  # a control, a mark, a direction change: never in the formula unseen
    return char
