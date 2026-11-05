"""What the LaTeX subset knows by name: sectioning levels, styles, dropped commands, environments.

Pure data shared by the command, environment and structure modules; nothing here runs.
"""

from clearmd.backend.services.conversion.tex.parsing import CODE_ENVIRONMENTS

SECTION_LEVELS = {
    "part": 0,
    "chapter": 1,
    "section": 2,
    "subsection": 3,
    "subsubsection": 4,
    "paragraph": 5,
    "subparagraph": 6,
}
INLINE = {
    "textbf": "**{}**",
    "textit": "*{}*",
    "textsl": "*{}*",
    "emph": "*{}*",
    "underline": "<u>{}</u>",
}
PLAIN = frozenset(
    {"textrm", "textsf", "textsc", "textup", "textmd", "textnormal", "mbox", "hbox", "text"}
)
# Layout and definitions: nothing to show (definitions are expanded by the macros package).
# Their arguments are declared in tex/parsing/specs.py, so they go with them.
DROPPED = frozenset(
    {
        "label", "index", "vspace", "hspace", "newpage", "clearpage", "cleardoublepage",
        "noindent", "centering", "tableofcontents", "listoffigures", "listoftables", "medskip",
        "bigskip", "smallskip", "vfill", "hfill", "linebreak", "pagebreak", "nopagebreak",
        "raggedright", "raggedleft", "documentclass", "usepackage", "graphicspath",
        "bibliographystyle", "bibliography", "printbibliography", "addbibresource", "pagestyle",
        "thispagestyle", "setlength", "setcounter", "addcontentsline", "phantomsection",
        "frontmatter", "mainmatter", "backmatter", "appendix", "thanks", "newcommand",
        "renewcommand", "providecommand", "DeclareMathOperator", "makeatletter", "makeatother",
        "small", "footnotesize", "large", "Large", "LARGE", "normalsize", "tiny", "huge", "Huge",
        "scriptsize", "bfseries", "itshape", "rmfamily", "sffamily", "ttfamily",
        "selectlanguage", "setmainlanguage", "onehalfspacing", "doublespacing", "singlespacing",
        "nocite", "hline", "toprule", "midrule", "bottomrule", "cline", "cmidrule", "today",
    }
)  # fmt: skip
METADATA = frozenset({"title", "author", "date"})
WORDS = {"LaTeXe": "LaTeX2e"}  # latex2text knows \LaTeX and \TeX
SPECIALS = {"~": " ", "--": "–", "---": "—", "``": "“", "''": "”", "!`": "¡", "?`": "¿"}
INCLUDES = frozenset({"input", "include", "subfile"})

LISTS = frozenset({"itemize", "enumerate", "description"})
QUOTES = frozenset({"quote", "quotation", "verse"})
CODE = frozenset(CODE_ENVIRONMENTS)
DISPLAY_MATH = frozenset({"equation", "equation*", "displaymath", "math"})
ALIGNED = {
    "align": "aligned",
    "align*": "aligned",
    "flalign": "aligned",
    "flalign*": "aligned",
    "eqnarray": "aligned",
    "eqnarray*": "aligned",
    "multline": "aligned",
    "multline*": "aligned",
    "gather": "gathered",
    "gather*": "gathered",
}
CONTAINERS = frozenset({"center", "flushleft", "flushright", "document"})
FLOATS = frozenset({"figure", "figure*", "wrapfigure", "table", "table*", "subfigure", "subtable"})
TABULARS = frozenset({"tabular", "tabular*", "tabularx", "longtable"})
LANGUAGES = frozenset(
    {
        "spanish", "english", "british", "american", "usenglish", "ukenglish", "french",
        "german", "ngerman", "italian", "portuguese", "brazil", "brazilian", "catalan",
        "basque", "galician",
    }
)  # fmt: skip
MAX_UNKNOWN = 1000  # distinct names kept for the note; the text keeps every one as written
