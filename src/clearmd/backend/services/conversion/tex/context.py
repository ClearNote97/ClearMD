r"""The parsing context: pylatexenc's defaults plus what ClearMD needs to read real documents.

pylatexenc does not know the arguments of many common commands (``\href``, ``\caption``,
``\paragraph``, ``\index``…), parses ``lstlisting`` and ``minted`` as ordinary LaTeX (a ``$`` in
code would become math), reads ``\url`` as LaTeX (a ``%`` would start a comment) and has no
``\def``. They are declared here; a parse error never stops the parse (tolerant mode), and the
first one is kept for the ``parse_recovered`` note.
"""

from dataclasses import dataclass
from typing import Any

from pylatexenc import latexwalker
from pylatexenc.macrospec import (
    EnvironmentSpec,
    LatexContextDb,
    MacroSpec,
    MacroStandardArgsParser,
    ParsedMacroArgs,
    ParsedVerbatimArgs,
)

CITATION_MACROS = ("cite", "citep", "citet", "parencite", "textcite", "autocite", "citeauthor")
REFERENCE_MACROS = ("ref", "eqref", "autoref", "cref", "Cref", "pageref", "nameref")
CODE_ENVIRONMENTS = ("verbatim", "verbatim*", "lstlisting", "minted")
_SPACE = " \t\n\r"


class Unparseable(Exception):
    """pylatexenc itself failed (not a LaTeX error it can recover from)."""


def _report(w: Any, pos: int, message: str) -> None:
    w._report_ignore_parse_error(latexwalker.LatexWalkerParseError(s=w.s, pos=pos, msg=message))


def _chars(w: Any, parsing_state: Any, start: int, end: int) -> Any:
    return w.make_node(
        latexwalker.LatexCharsNode,
        parsing_state=parsing_state,
        chars=w.s[start:end],
        pos=start,
        len=end - start,
    )


def _balanced_end(text: str, start: int) -> int:
    """The index of the ``}`` closing the ``{`` at ``start`` (escaped braces skipped), or -1."""
    depth = 0
    index = start
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return -1


class CmidruleParser(MacroStandardArgsParser):  # type: ignore[misc]
    r"""``\cmidrule[w](lr){a-b}``: all of it is a rule, nothing to show."""

    def __init__(self) -> None:
        super().__init__(argspec="")

    def parse_args(self, w: Any, pos: int, parsing_state: Any = None) -> tuple[Any, int, int]:
        stop = pos
        for opening, closing in (("[", "]"), ("(", ")"), ("{", "}")):
            while stop < len(w.s) and w.s[stop] in _SPACE:
                stop += 1
            if w.s.startswith(opening, stop):
                end = w.s.find(closing, stop)
                if end == -1:
                    break
                stop = end + 1
        return ParsedMacroArgs(argspec="", argnlist=[]), pos, stop - pos


class VerbatimEnvironmentParser(MacroStandardArgsParser):  # type: ignore[misc]
    r"""Everything up to ``\end{<name>}``, untouched; without that ``\end``, the rest."""

    def __init__(self, name: str) -> None:
        super().__init__(argspec="")
        self.name = name

    def parse_args(self, w: Any, pos: int, parsing_state: Any = None) -> tuple[Any, int, int]:
        end = w.s.find(f"\\end{{{self.name}}}", pos)
        if end == -1:
            _report(w, pos, f"Cannot find matching \\end{{{self.name}}}")
            end = len(w.s)
        node = _chars(w, parsing_state, pos, end)
        return ParsedVerbatimArgs(verbatim_chars_node=node), pos, end - pos


class VerbParser(MacroStandardArgsParser):  # type: ignore[misc]
    r"""``\verb|…|`` and ``\verb*|…|`` on one line; anything else leaves no argument."""

    def __init__(self) -> None:
        super().__init__(argspec="")

    def parse_args(self, w: Any, pos: int, parsing_state: Any = None) -> tuple[Any, int, int]:
        start = pos + 1 if w.s.startswith("*", pos) else pos
        delimiter = w.s[start : start + 1]
        end = w.s.find(delimiter, start + 1) if delimiter and not delimiter.isalpha() else -1
        newline = w.s.find("\n", start + 1)
        if end == -1 or (newline != -1 and newline < end) or delimiter in _SPACE:
            _report(w, pos, "\\verb without its closing delimiter")
            return ParsedMacroArgs(argspec="", argnlist=[]), pos, 0
        node = _chars(w, parsing_state, start + 1, end)
        args = ParsedVerbatimArgs(verbatim_chars_node=node, verbatim_delimiters=(delimiter,) * 2)
        return args, pos, end + 1 - pos


class UrlArgsParser(MacroStandardArgsParser):  # type: ignore[misc]
    r"""A first ``{…}`` read as written (``%`` and ``#`` belong to a URL), then ``rest``."""

    def __init__(self, rest: str = "") -> None:
        super().__init__(argspec="{" + rest)
        self.rest = rest

    def parse_args(self, w: Any, pos: int, parsing_state: Any = None) -> tuple[Any, int, int]:
        start = pos
        while start < len(w.s) and w.s[start] in _SPACE:
            start += 1
        end = _balanced_end(w.s, start) if w.s.startswith("{", start) else -1
        if end == -1:
            _report(w, pos, "URL without its closing brace")
            return ParsedMacroArgs(argspec="", argnlist=[]), pos, 0
        url = _chars(w, parsing_state, start + 1, end)
        arguments = [url]
        stop = end + 1
        if self.rest:
            more, more_pos, more_len = MacroStandardArgsParser(argspec=self.rest).parse_args(
                w, stop, parsing_state=parsing_state
            )
            arguments.extend(more.argnlist)
            stop = more_pos + more_len
        return ParsedMacroArgs(argspec=self.argspec, argnlist=arguments), pos, stop - pos


@dataclass(frozen=True)
class ParsedDef:
    name: str
    parameters: str
    body: Any


class DefParser(MacroStandardArgsParser):  # type: ignore[misc]
    r"""``\def\name<parameters>{body}`` as one node, whatever ``\name`` means elsewhere."""

    def __init__(self) -> None:
        super().__init__(argspec="")

    def parse_args(self, w: Any, pos: int, parsing_state: Any = None) -> tuple[Any, int, int]:
        start = pos
        while start < len(w.s) and w.s[start] in _SPACE:
            start += 1
        name_end = start + 1
        while name_end < len(w.s) and w.s[name_end].isalpha():
            name_end += 1
        if not w.s.startswith("\\", start) or name_end == start + 1:
            _report(w, pos, "\\def without a command name")
            return ParsedMacroArgs(argspec="", argnlist=[]), pos, 0
        brace = w.s.find("{", name_end)
        end = _balanced_end(w.s, brace) if brace != -1 else -1
        if end == -1:
            _report(w, pos, "\\def without its body")
            return ParsedMacroArgs(argspec="", argnlist=[]), pos, 0
        body = _chars(w, parsing_state, brace + 1, end)
        args = ParsedMacroArgs(argspec="", argnlist=[])
        args.clearmd_def = ParsedDef(w.s[start + 1 : name_end], w.s[name_end:brace], body)
        return args, pos, end + 1 - pos


_MACROS = [
    MacroSpec("verb", args_parser=VerbParser()),
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
    MacroSpec("DeclareMathOperator", "*{{"),
    MacroSpec("newcommand", "*{[[{"),
    MacroSpec("renewcommand", "*{[[{"),
    MacroSpec("providecommand", "*{[[{"),
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
    MacroSpec("cline", "{"),
    MacroSpec("cmidrule", args_parser=CmidruleParser()),
    *(MacroSpec(name, "*[[{") for name in CITATION_MACROS),
    *(MacroSpec(name, "{") for name in REFERENCE_MACROS),
]
_ENVIRONMENTS = [
    *(
        EnvironmentSpec(name, args_parser=VerbatimEnvironmentParser(name))
        for name in CODE_ENVIRONMENTS
    ),
    EnvironmentSpec("longtable", "[{"),
    EnvironmentSpec("subfigure", "[{"),
    EnvironmentSpec("minipage", "[[[{"),
]


def make_context(extra_macros: list[Any] | None = None) -> LatexContextDb:
    """A fresh context: pylatexenc's defaults, ClearMD's additions, then the author's macros."""
    context = latexwalker.get_default_latex_context_db()
    context.add_context_category(
        "clearmd", macros=_MACROS, environments=_ENVIRONMENTS, prepend=True
    )
    if extra_macros:
        context.add_context_category("author", macros=extra_macros, prepend=True)
    return context


class _Walker(latexwalker.LatexWalker):  # type: ignore[misc]
    """A tolerant walker that keeps the first error it recovered from."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.first_error: latexwalker.LatexWalkerParseError | None = None

    def _report_ignore_parse_error(self, exc: Any) -> None:
        if self.first_error is None:
            self.first_error = exc


@dataclass(frozen=True)
class ParseError:
    position: int
    message: str


def parse(text: str, context: LatexContextDb) -> tuple[list[Any], ParseError | None]:
    """The nodes of ``text`` and the first error recovered from; ``Unparseable`` otherwise."""
    walker = _Walker(text, latex_context=context, tolerant_parsing=True)
    try:
        nodes, _, _ = walker.get_latex_nodes()
    except (RecursionError, IndexError, ValueError, latexwalker.LatexWalkerError) as error:
        raise Unparseable(type(error).__name__) from error
    found = walker.first_error
    if found is None:
        return list(nodes), None
    message = str(getattr(found, "msg", None) or found).splitlines()[0]
    return list(nodes), ParseError(int(getattr(found, "pos", 0) or 0), message)
