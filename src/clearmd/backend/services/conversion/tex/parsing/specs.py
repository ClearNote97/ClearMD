"""The macros and environments pylatexenc does not know, and the context that holds them."""

from typing import Any

from pylatexenc import latexwalker
from pylatexenc.macrospec import EnvironmentSpec, LatexContextDb, MacroSpec

from clearmd.backend.services.conversion.tex.parsing.definition_args import DefParser, RawBodyParser
from clearmd.backend.services.conversion.tex.parsing.verbatim_args import (
    CmidruleParser,
    UrlArgsParser,
    VerbatimEnvironmentParser,
    VerbParser,
)

CITATION_MACROS = ("cite", "citep", "citet", "parencite", "textcite", "autocite", "citeauthor")


REFERENCE_MACROS = ("ref", "eqref", "autoref", "cref", "Cref", "pageref", "nameref")


CODE_ENVIRONMENTS = (
    "verbatim",
    "verbatim*",
    "lstlisting",
    "minted",
    "Verbatim",
    "Verbatim*",
    "BVerbatim",
    "LVerbatim",
)


MACROS = [
    MacroSpec("verb", args_parser=VerbParser()),
    MacroSpec("lstinline", args_parser=VerbParser(options=True)),
    MacroSpec("def", args_parser=DefParser()),
    MacroSpec("url", args_parser=UrlArgsParser()),
    MacroSpec("href", args_parser=UrlArgsParser("{")),
    MacroSpec("part", "*[{"),
    MacroSpec("paragraph", "*[{"),
    MacroSpec("caption", "*[{"),
    MacroSpec("graphicspath", "{"),
    MacroSpec("include", "{"),
    MacroSpec("subfile", "{"),
    MacroSpec("underline", "{"),
    MacroSpec("includegraphics", "*[[{"),
    MacroSpec("DeclareMathOperator", args_parser=RawBodyParser("*{")),
    MacroSpec("newcommand", args_parser=RawBodyParser("*{[[")),
    MacroSpec("renewcommand", args_parser=RawBodyParser("*{[[")),
    MacroSpec("providecommand", args_parser=RawBodyParser("*{[[")),
    # Dropped commands: their arguments go with them.
    MacroSpec("index", "[{"),
    MacroSpec("thanks", "{"),
    MacroSpec("addcontentsline", "{{{"),
    MacroSpec("pagestyle", "{"),
    MacroSpec("thispagestyle", "{"),
    MacroSpec("bibliographystyle", "{"),
    MacroSpec("bibliography", "{"),
    MacroSpec("addbibresource", "[{"),
    MacroSpec("printbibliography", "["),
    MacroSpec("nocite", "{"),
    MacroSpec("setmainlanguage", "[{"),
    MacroSpec("setdefaultlanguage", "[{"),
    MacroSpec("cline", "{"),
    MacroSpec("cmidrule", args_parser=CmidruleParser()),
    *(MacroSpec(name, "*[[{") for name in CITATION_MACROS),
    *(MacroSpec(name, "{") for name in REFERENCE_MACROS),
]


ENVIRONMENTS = [
    *(
        EnvironmentSpec(name, args_parser=VerbatimEnvironmentParser(name))
        for name in CODE_ENVIRONMENTS
    ),
    EnvironmentSpec("comment", args_parser=VerbatimEnvironmentParser("comment")),
    EnvironmentSpec("longtable", "[{"),
    EnvironmentSpec("subfigure", "[{"),
    EnvironmentSpec("minipage", "[[[{"),
]


def make_context(extra_macros: list[Any] | None = None) -> LatexContextDb:
    """A fresh context: pylatexenc's defaults, ClearMD's additions, then the author's macros."""
    context = latexwalker.get_default_latex_context_db()
    context.add_context_category("clearmd", macros=MACROS, environments=ENVIRONMENTS, prepend=True)
    if extra_macros:
        context.add_context_category("author", macros=extra_macros, prepend=True)
    return context
