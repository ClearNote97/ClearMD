r"""The parsing context: pylatexenc's defaults plus what ClearMD needs to read real documents.

pylatexenc does not know the arguments of many common commands (``\href``, ``\caption``,
``\paragraph``, ``\index``…), parses ``lstlisting`` and ``minted`` as ordinary LaTeX (a ``$`` in
code would become math), reads ``\url`` as LaTeX (a ``%`` would start a comment) and has no
``\def``. They are declared here; a parse error never stops the parse (tolerant mode), and the
first one is kept for the ``parse_recovered`` note.
"""

import bisect
import re
from array import array
from dataclasses import dataclass
from functools import lru_cache
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
VERB_WINDOW = 4096  # a \verb argument is on one line; never searched farther than this
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


_SMALL_TEXT = 4096  # scanned directly; larger texts get their pairs computed once


def _scan_end(text: str, start: int, comments: bool) -> int:
    depth = 0
    index = start
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "%" and comments:
            line_end = text.find("\n", index)
            if line_end == -1:
                return -1
            index = line_end + 1
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return -1


@lru_cache(maxsize=4)
def _brace_pairs(text: str, comments: bool) -> tuple[array[int], array[int]]:
    """Every matched ``{`` of a large text and its ``}``, in one pass: two compact arrays
    (opening positions, sorted, and their closings), about 16 bytes per pair."""
    pairs: list[tuple[int, int]] = []
    open_at: list[int] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "%" and comments:
            line_end = text.find("\n", index)
            index = len(text) if line_end == -1 else line_end + 1
            continue
        if char == "{":
            open_at.append(index)
        elif char == "}" and open_at:
            pairs.append((open_at.pop(), index))
        index += 1
    pairs.sort()
    return array("q", (o for o, _ in pairs)), array("q", (c for _, c in pairs))


def forget_brace_pairs() -> None:
    """Free the pairs kept for the large texts of the document just converted."""
    _brace_pairs.cache_clear()


def _balanced_end(text: str, start: int, *, comments: bool = True) -> int:
    """The index of the ``}`` closing the ``{`` at ``start``, or -1. Linear over a document:
    a large text's pairs are found once, not once per unclosed brace."""
    if len(text) < _SMALL_TEXT:
        return _scan_end(text, start, comments)
    openings, closings = _brace_pairs(text, comments)
    index = bisect.bisect_left(openings, start)
    return closings[index] if index < len(openings) and openings[index] == start else -1


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
    r"""``\verb|…|`` and ``\verb*|…|`` on one line; ``\lstinline[opts]|…|`` or ``{…}`` too.
    Anything else leaves no argument."""

    def __init__(self, *, options: bool = False) -> None:
        super().__init__(argspec="")
        self.options = options

    def parse_args(self, w: Any, pos: int, parsing_state: Any = None) -> tuple[Any, int, int]:
        start = pos + 1 if w.s.startswith("*", pos) else pos
        if self.options and w.s.startswith("[", start):
            closing = w.s.find("]", start, start + VERB_WINDOW)
            start = closing + 1 if closing != -1 else start
        delimiter = w.s[start : start + 1]
        limit = min(len(w.s), start + VERB_WINDOW)
        newline = w.s.find("\n", start + 1, limit)
        limit = newline if newline != -1 else limit
        closer = "}" if self.options and delimiter == "{" else delimiter
        usable = delimiter and not delimiter.isalpha() and delimiter not in _SPACE
        end = w.s.find(closer, start + 1, limit) if usable else -1
        if end == -1:
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
        found = w.s.startswith("{", start)
        end = _balanced_end(w.s, start, comments=False) if found else -1
        if end == -1:
            _report(w, pos, "URL without its closing brace")
            empty = [None] * len(self.argspec)  # every argument absent, never a short list
            return ParsedMacroArgs(argspec=self.argspec, argnlist=empty), pos, 0
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
        while name_end < len(w.s) and (w.s[name_end].isalpha() or w.s[name_end] == "@"):
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


class RawBodyParser(MacroStandardArgsParser):  # type: ignore[misc]
    r"""``head`` arguments, then a ``{body}`` kept as written: a body like ``\begin{equation}``
    must not open an environment in the definition and swallow the rest of the document."""

    def __init__(self, head: str) -> None:
        super().__init__(argspec=head + "{")
        self.head = head

    def parse_args(self, w: Any, pos: int, parsing_state: Any = None) -> tuple[Any, int, int]:
        first, first_pos, first_len = MacroStandardArgsParser(argspec=self.head).parse_args(
            w, pos, parsing_state=parsing_state
        )
        start = first_pos + first_len
        while start < len(w.s) and w.s[start] in _SPACE:
            start += 1
        end = _balanced_end(w.s, start) if w.s.startswith("{", start) else -1
        if end == -1:
            _report(w, pos, "definition without its body")
            arguments = [*first.argnlist, None]
            return ParsedMacroArgs(argspec=self.argspec, argnlist=arguments), pos, start - pos
        body = _chars(w, parsing_state, start + 1, end)
        arguments = [*first.argnlist, body]
        return ParsedMacroArgs(argspec=self.argspec, argnlist=arguments), pos, end + 1 - pos


_MACROS = [
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
_ENVIRONMENTS = [
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


# What is not LaTeX to look into for includes: comments (a "%" after an even run of backslashes),
# code environments, the comment environment, \verb and \lstinline, \iffalse … \fi (nested
# conditionals counted) and URL arguments.
_NOT_SOURCE = re.compile(
    r"(?<!\\)(?:\\\\)*%"
    r"|\\begin\s*\{(verbatim\*?|Verbatim\*?|BVerbatim|LVerbatim|lstlisting|minted|comment)\}"
    r"|\\(?:verb\*?|lstinline(?:\[[^\]\n]{0,256}\])?)([^\sA-Za-z*])"
    r"|\\iffalse(?![A-Za-z@])"
    r"|\\(?:url|href)\s*(?=\{)"
)
# \ifthenelse is a macro of the ifthen package, not a TeX conditional: it has no \fi.
_CONDITIONAL = re.compile(r"\\(if(?!thenelse)[A-Za-z@]*|fi)(?![A-Za-z@])")


def matching_fi(text: str, start: int) -> int | None:
    r"""The end of the ``\fi`` closing a conditional opened just before ``start`` (nested ones
    counted), or ``None``."""
    depth = 1
    for found in _CONDITIONAL.finditer(text, start):
        depth += -1 if found.group(1) == "fi" else 1
        if depth == 0:
            return found.end()
    return None


def mask(text: str) -> str:
    """``text`` with what is not source replaced by spaces (same length, newlines kept)."""
    pieces, cursor = [], 0
    while (found := _NOT_SOURCE.search(text, cursor)) is not None:
        start, token = found.start(), found.group(0)
        if token.endswith("%"):
            start = found.end() - 1
            line_end = text.find("\n", start)
            end = len(text) if line_end == -1 else line_end
        elif found.group(1):
            close = text.find(f"\\end{{{found.group(1)}}}", found.end())
            end = len(text) if close == -1 else close
        elif found.group(2):
            delimiter = "}" if found.group(2) == "{" else found.group(2)
            limit = min(len(text), found.end() + VERB_WINDOW)
            line_end = text.find("\n", found.end(), limit)
            close = text.find(delimiter, found.end(), limit if line_end == -1 else line_end)
            end = found.end() if close == -1 else close + 1
        elif token.startswith("\\iffalse"):
            fi = matching_fi(text, found.end())
            end = found.end() if fi is None else fi  # unclosed: not a comment (noted when read)
        else:  # \url{…} or \href{…}: read as written by UrlArgsParser
            close = _balanced_end(text, found.end(), comments=False)
            end = found.end() if close == -1 else close + 1
        pieces.append(text[cursor:start])
        pieces.append(re.sub(r"[^\n]", " ", text[start:end]))
        cursor = max(end, found.end())
    pieces.append(text[cursor:])
    return "".join(pieces)
