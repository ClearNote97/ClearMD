r"""Argument parsers for definitions: ``\def`` and the ``\newcommand`` family, body kept raw."""

from dataclasses import dataclass
from typing import Any

from pylatexenc.macrospec import MacroStandardArgsParser, ParsedMacroArgs

from clearmd.backend.services.conversion.tex.parsing.braces import balanced_end
from clearmd.backend.services.conversion.tex.parsing.cursor import SPACE, chars, report


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
        while start < len(w.s) and w.s[start] in SPACE:
            start += 1
        name_end = start + 1
        while name_end < len(w.s) and (w.s[name_end].isalpha() or w.s[name_end] == "@"):
            name_end += 1
        if not w.s.startswith("\\", start) or name_end == start + 1:
            report(w, pos, "\\def without a command name")
            return ParsedMacroArgs(argspec="", argnlist=[]), pos, 0
        brace = w.s.find("{", name_end)
        end = balanced_end(w.s, brace) if brace != -1 else -1
        if end == -1:
            report(w, pos, "\\def without its body")
            return ParsedMacroArgs(argspec="", argnlist=[]), pos, 0
        body = chars(w, parsing_state, brace + 1, end)
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
        while start < len(w.s) and w.s[start] in SPACE:
            start += 1
        end = balanced_end(w.s, start) if w.s.startswith("{", start) else -1
        if end == -1:
            report(w, pos, "definition without its body")
            arguments = [*first.argnlist, None]
            return ParsedMacroArgs(argspec=self.argspec, argnlist=arguments), pos, start - pos
        body = chars(w, parsing_state, start + 1, end)
        arguments = [*first.argnlist, body]
        return ParsedMacroArgs(argspec=self.argspec, argnlist=arguments), pos, end + 1 - pos
