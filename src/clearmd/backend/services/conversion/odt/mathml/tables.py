"""The tables of the MathML subset: Greek letters, symbols, functions, accents, fences.

It stands alone because it is data only: every other module of the package reads it.
"""

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
LATEX_SPECIAL = {"{": "\\{", "}": "\\}", "#": "\\#", "%": "\\%", "&": "\\&", "$": "\\$",
                  "_": "\\_", "\\": "\\backslash", "~": "\\sim", "^": "\\hat{}"}  # fmt: skip
TEXT_SPECIAL = {"{": "\\{", "}": "\\}", "#": "\\#", "%": "\\%", "&": "\\&", "$": "\\$",
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
