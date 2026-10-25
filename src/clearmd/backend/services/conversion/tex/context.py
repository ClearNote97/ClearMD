r"""The parsing context: pylatexenc's defaults plus what ClearMD needs to read real documents.

pylatexenc does not know the arguments of ``\href`` or ``\caption`` and parses ``lstlisting`` and
``minted`` as ordinary LaTeX (a ``$`` in code would become math), so they are declared here.
"""

from typing import Any

from pylatexenc import latexwalker
from pylatexenc.macrospec import (
    EnvironmentSpec,
    LatexContextDb,
    MacroSpec,
    MacroStandardArgsParser,
    ParsedVerbatimArgs,
)


class VerbatimEnvironmentParser(MacroStandardArgsParser):  # type: ignore[misc]
    r"""Everything up to ``\end{<name>}``, untouched (pylatexenc hard-codes ``verbatim``)."""

    def __init__(self, name: str) -> None:
        super().__init__(argspec="")
        self.name = name

    def parse_args(self, w: Any, pos: int, parsing_state: Any = None) -> tuple[Any, int, int]:
        end = w.s.find(f"\\end{{{self.name}}}", pos)
        if end == -1:
            raise latexwalker.LatexWalkerParseError(
                s=w.s, pos=pos, msg=f"Cannot find matching \\end{{{self.name}}}"
            )
        chars = w.make_node(
            latexwalker.LatexCharsNode,
            parsing_state=parsing_state,
            chars=w.s[pos:end],
            pos=pos,
            len=end - pos,
        )
        return ParsedVerbatimArgs(verbatim_chars_node=chars), pos, end - pos


CITATION_MACROS = ("cite", "citep", "citet", "parencite", "textcite", "autocite", "citeauthor")
REFERENCE_MACROS = ("ref", "eqref", "autoref", "cref", "Cref", "pageref", "nameref")

_MACROS = [
    MacroSpec("href", "{{"),
    MacroSpec("caption", "[{"),
    MacroSpec("graphicspath", "{"),
    MacroSpec("include", "{"),
    MacroSpec("subfile", "{"),
    MacroSpec("underline", "{"),
    MacroSpec("DeclareMathOperator", "*{{"),
    MacroSpec("newcommand", "*{[[{"),
    MacroSpec("renewcommand", "*{[[{"),
    MacroSpec("providecommand", "*{[[{"),
    *(MacroSpec(name, "*[[{") for name in CITATION_MACROS),
    *(MacroSpec(name, "{") for name in REFERENCE_MACROS),
]
_ENVIRONMENTS = [
    EnvironmentSpec("lstlisting", args_parser=VerbatimEnvironmentParser("lstlisting")),
    EnvironmentSpec("minted", args_parser=VerbatimEnvironmentParser("minted")),
]


class _SkipStrict(Exception):
    pass


def make_context(extra_macros: list[Any] | None = None) -> LatexContextDb:
    """A fresh context: pylatexenc's defaults, ClearMD's additions, then the author's macros."""
    context = latexwalker.get_default_latex_context_db()
    context.add_context_category(
        "clearmd", macros=_MACROS, environments=_ENVIRONMENTS, prepend=True
    )
    if extra_macros:
        context.add_context_category("author", macros=extra_macros, prepend=True)
    return context


def parse(
    text: str, context: LatexContextDb, *, strict: bool = True
) -> tuple[list[Any], str | None]:
    """The nodes of ``text``, and the first parse error (the tolerant parse recovers from it).

    ``strict=False`` skips the strict pass that only reports errors (macro expansions).
    """
    error: str | None = None
    try:
        if not strict:
            raise _SkipStrict
        latexwalker.LatexWalker(
            text, latex_context=context, tolerant_parsing=False
        ).get_latex_nodes()
    except _SkipStrict:
        pass
    except latexwalker.LatexWalkerError as problem:
        error = str(problem).splitlines()[0]
    walker = latexwalker.LatexWalker(text, latex_context=context, tolerant_parsing=True)
    nodes, _, _ = walker.get_latex_nodes()
    return list(nodes), error
