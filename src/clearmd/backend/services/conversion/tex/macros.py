r"""The author's own macros: collected in document order, expanded with a budget (ADR-0022).

Expanded: ``\newcommand``/``\renewcommand``/``\providecommand`` (up to 9 arguments, an optional
first one with its default), ``\DeclareMathOperator`` and ``\def`` without parameters. A macro bomb
(recursive or exponential) hits the budget, stops expanding, and is reported.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from pylatexenc.latexwalker import LatexGroupNode, LatexMacroNode
from pylatexenc.macrospec import MacroSpec

from clearmd.backend.schemas.notes import NoteReason
from clearmd.backend.services.conversion.tex.context import make_context, parse

MAX_EXPANSIONS = 10_000
MAX_NESTING = 64
GROWTH_FACTOR = 4
GROWTH_EXTRA = 1024**2
_CACHE_ENTRIES = 4096
DEFINING = frozenset({"newcommand", "renewcommand", "providecommand"})


@dataclass(frozen=True)
class MacroDefinition:
    name: str
    arguments: int
    default: str | None
    body: str

    @property
    def argspec(self) -> str:
        if self.arguments == 0:
            return ""
        if self.default is not None:
            return "[" + "{" * (self.arguments - 1)
        return "{" * self.arguments


class BudgetExceeded(Exception):
    def __init__(self, reason: NoteReason) -> None:
        super().__init__(reason.value)
        self.reason = reason


def _inner(node: Any) -> str:
    if node is None:
        return ""
    if isinstance(node, LatexGroupNode):
        return "".join(child.latex_verbatim() for child in node.nodelist or [])
    text: str = node.latex_verbatim()
    return text


def _defined_name(node: Any) -> str | None:
    if isinstance(node, LatexMacroNode):
        name: str = node.macroname
        return name
    if isinstance(node, LatexGroupNode):
        macros = [n for n in node.nodelist or [] if isinstance(n, LatexMacroNode)]
        return str(macros[0].macroname) if macros else None
    return None


def collect_definitions(nodes: list[Any]) -> dict[str, MacroDefinition]:
    """Every definition, in document order (renew replaces, provide keeps the first)."""
    found: dict[str, MacroDefinition] = {}

    def visit(siblings: list[Any]) -> None:
        for index, node in enumerate(siblings):
            if node is None:
                continue
            if isinstance(node, LatexMacroNode):
                _definition(node, siblings[index + 1 : index + 3], found)
            visit(list(getattr(node, "nodelist", None) or []))

    visit(nodes)
    return found


def _definition(node: Any, following: list[Any], found: dict[str, MacroDefinition]) -> None:
    arguments = getattr(getattr(node, "nodeargd", None), "argnlist", None) or []
    if node.macroname in DEFINING and len(arguments) == 5:
        name = _defined_name(arguments[1])
        if name is None:
            return
        count_text = _inner(arguments[2]).strip()
        count = int(count_text) if count_text.isdigit() and 0 < int(count_text) <= 9 else 0
        default = _inner(arguments[3]) if arguments[3] is not None else None
        definition = MacroDefinition(name, count, default if count else None, _inner(arguments[4]))
        if node.macroname == "providecommand" and name in found:
            return
        found[name] = definition
    elif node.macroname == "DeclareMathOperator" and len(arguments) == 3:
        name = _defined_name(arguments[1])
        if name is not None:
            star = "*" if arguments[0] is not None else ""
            found[name] = MacroDefinition(
                name, 0, None, f"\\operatorname{star}{{{_inner(arguments[2])}}}"
            )
    elif node.macroname == "def" and len(following) == 2:
        name_node, body = following
        if isinstance(name_node, LatexMacroNode) and isinstance(body, LatexGroupNode):
            found[name_node.macroname] = MacroDefinition(name_node.macroname, 0, None, _inner(body))


def substitute(definition: MacroDefinition, values: list[str]) -> str:
    body = definition.body
    for position in range(definition.arguments, 0, -1):
        value = values[position - 1] if position - 1 < len(values) else ""
        body = body.replace(f"#{position}", value)
    return body


class MacroExpander:
    def __init__(self, definitions: dict[str, MacroDefinition], source_size: int) -> None:
        self.definitions = definitions
        specs = [MacroSpec(name, d.argspec) for name, d in definitions.items()]
        self.context = make_context(specs)
        self.limit_growth = GROWTH_FACTOR * source_size + GROWTH_EXTRA
        self.expansions = 0
        self.produced = 0
        self.depth = 0
        self.exhausted: NoteReason | None = None
        self.limited: str | None = None  # the top-level use that hit the budget first
        self._cache: dict[str, list[Any]] = {}

    def knows(self, name: str) -> bool:
        return name in self.definitions

    def _exceed(self, reason: NoteReason) -> None:
        if self.exhausted is None:
            self.exhausted = reason
        raise BudgetExceeded(self.exhausted)

    @contextmanager
    def nested(self) -> Iterator[None]:
        self.depth += 1
        try:
            if self.depth > MAX_NESTING:
                self._exceed(NoteReason.NESTING)
            yield
        finally:
            self.depth -= 1

    def expand(self, node: Any) -> list[Any]:
        """The nodes a use of an author's macro stands for (charged to the budget)."""
        if self.exhausted is not None:
            raise BudgetExceeded(self.exhausted)
        definition = self.definitions[node.macroname]
        arguments = getattr(getattr(node, "nodeargd", None), "argnlist", None) or []
        values = [_inner(argument) if argument is not None else None for argument in arguments]
        if definition.default is not None and values and values[0] is None:
            values[0] = definition.default
        text = substitute(definition, [value or "" for value in values])
        self.expansions += 1
        if self.expansions > MAX_EXPANSIONS:
            self._exceed(NoteReason.EXPANSIONS)
        self.produced += len(text)
        if self.produced > self.limit_growth:
            self._exceed(NoteReason.GROWTH)
        cached = self._cache.get(text)
        if cached is None:
            cached, _ = parse(text, self.context, strict=False)
            if len(self._cache) < _CACHE_ENTRIES:
                self._cache[text] = cached
        return cached
