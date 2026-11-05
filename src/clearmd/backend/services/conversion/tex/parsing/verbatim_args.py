r"""Parsers that read their text as written: rules, verbatim environments, ``\verb``, URLs."""

from typing import Any

from pylatexenc.macrospec import MacroStandardArgsParser, ParsedMacroArgs, ParsedVerbatimArgs

from clearmd.backend.services.conversion.tex.parsing.braces import balanced_end
from clearmd.backend.services.conversion.tex.parsing.cursor import SPACE, VERB_WINDOW, chars, report


class CmidruleParser(MacroStandardArgsParser):  # type: ignore[misc]
    r"""``\cmidrule[w](lr){a-b}``: all of it is a rule, nothing to show."""

    def __init__(self) -> None:
        super().__init__(argspec="")

    def parse_args(self, w: Any, pos: int, parsing_state: Any = None) -> tuple[Any, int, int]:
        stop = pos
        for opening, closing in (("[", "]"), ("(", ")"), ("{", "}")):
            while stop < len(w.s) and w.s[stop] in SPACE:
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
            report(w, pos, f"Cannot find matching \\end{{{self.name}}}")
            end = len(w.s)
        node = chars(w, parsing_state, pos, end)
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
        usable = delimiter and not delimiter.isalpha() and delimiter not in SPACE
        end = w.s.find(closer, start + 1, limit) if usable else -1
        if end == -1:
            report(w, pos, "\\verb without its closing delimiter")
            return ParsedMacroArgs(argspec="", argnlist=[]), pos, 0
        node = chars(w, parsing_state, start + 1, end)
        args = ParsedVerbatimArgs(verbatim_chars_node=node, verbatim_delimiters=(delimiter,) * 2)
        return args, pos, end + 1 - pos


class UrlArgsParser(MacroStandardArgsParser):  # type: ignore[misc]
    r"""A first ``{…}`` read as written (``%`` and ``#`` belong to a URL), then ``rest``."""

    def __init__(self, rest: str = "") -> None:
        super().__init__(argspec="{" + rest)
        self.rest = rest

    def parse_args(self, w: Any, pos: int, parsing_state: Any = None) -> tuple[Any, int, int]:
        start = pos
        while start < len(w.s) and w.s[start] in SPACE:
            start += 1
        found = w.s.startswith("{", start)
        end = balanced_end(w.s, start, comments=False) if found else -1
        if end == -1:
            report(w, pos, "URL without its closing brace")
            empty = [None] * len(self.argspec)  # every argument absent, never a short list
            return ParsedMacroArgs(argspec=self.argspec, argnlist=empty), pos, 0
        url = chars(w, parsing_state, start + 1, end)
        arguments = [url]
        stop = end + 1
        if self.rest:
            more, more_pos, more_len = MacroStandardArgsParser(argspec=self.rest).parse_args(
                w, stop, parsing_state=parsing_state
            )
            arguments.extend(more.argnlist)
            stop = more_pos + more_len
        return ParsedMacroArgs(argspec=self.argspec, argnlist=arguments), pos, stop - pos
