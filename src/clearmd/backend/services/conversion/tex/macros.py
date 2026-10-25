r"""The author's own macros: collected in document order, expanded with a budget (ADR-0022).

Expanded: ``\newcommand``/``\renewcommand``/``\providecommand`` (up to 9 arguments, an optional
first one with its default), ``\DeclareMathOperator`` and ``\def`` without parameters. ``#1`` …
``#9`` are replaced in one pass (what an argument brings is never replaced again; ``##`` is
``#``), and the size of an expansion is charged to the budget before the text is built, so a macro
bomb (recursive, exponential or wide) hits the budget, stops expanding, and is reported.
"""

import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
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
_PARAMETER = re.compile(r"#([1-9#])")


@dataclass(frozen=True)
class MacroDefinition:
    name: str
    arguments: int
    default: str | None
    body: str
    uses: tuple[int, ...] = field(init=False)  # how many times #1 … #9 appear in the body

    def __post_init__(self) -> None:
        found = _PARAMETER.findall(self.body)
        object.__setattr__(
            self, "uses", tuple(found.count(str(n)) for n in range(1, self.arguments + 1))
        )

    @property
    def argspec(self) -> str:
        if self.arguments == 0:
            return ""
        if self.default is not None:
            return "[" + "{" * (self.arguments - 1)
        return "{" * self.arguments

    def size(self, values: list[str]) -> int:
        """The length of the expansion, without building it."""
        size = len(self.body) - 2 * sum(self.uses) - self.body.count("##")
        return size + sum(len(value) * uses for value, uses in zip(values, self.uses, strict=False))

    def substitute(self, values: list[str]) -> str:
        def replace(match: re.Match[str]) -> str:
            mark = match.group(1)
            if mark == "#":
                return "#"
            index = int(mark) - 1
            return values[index] if index < min(len(values), self.arguments) else match.group(0)

        return _PARAMETER.sub(replace, self.body)


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


def _children(node: Any) -> list[Any]:
    arguments = getattr(getattr(node, "nodeargd", None), "argnlist", None) or []
    return [*(getattr(node, "nodelist", None) or []), *arguments]


def collect_definitions(nodes: list[Any]) -> dict[str, MacroDefinition]:
    """Every definition, in document order (renew replaces, provide keeps the first)."""
    found: dict[str, MacroDefinition] = {}
    pending = list(reversed(nodes))
    while pending:  # depth-first, in document order, without recursion
        node = pending.pop()
        if node is None:
            continue
        if isinstance(node, LatexMacroNode):
            _definition(node, found)
        pending.extend(reversed(_children(node)))
    return found


def _definition(node: Any, found: dict[str, MacroDefinition]) -> None:
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
            body = f"\\operatorname{star}{{{_inner(arguments[2])}}}"
            found[name] = MacroDefinition(name, 0, None, body)
    elif node.macroname == "def":
        parsed = getattr(node.nodeargd, "clearmd_def", None)
        if parsed is not None and not parsed.parameters.strip():
            found[parsed.name] = MacroDefinition(parsed.name, 0, None, parsed.body.chars)


def is_parametrized_def(node: Any) -> bool:
    parsed = getattr(getattr(node, "nodeargd", None), "clearmd_def", None)
    return parsed is None or bool(parsed.parameters.strip())


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
        """The nodes a use of an author's macro stands for (charged to the budget first)."""
        if self.exhausted is not None:
            raise BudgetExceeded(self.exhausted)
        definition = self.definitions[node.macroname]
        arguments = getattr(getattr(node, "nodeargd", None), "argnlist", None) or []
        values = [_inner(argument) if argument is not None else None for argument in arguments]
        if definition.default is not None and values and values[0] is None:
            values[0] = definition.default
        filled = [value or "" for value in values]
        self.expansions += 1
        if self.expansions > MAX_EXPANSIONS:
            self._exceed(NoteReason.EXPANSIONS)
        self.produced += definition.size(filled)
        if self.produced > self.limit_growth:
            self._exceed(NoteReason.GROWTH)
        text = definition.substitute(filled)
        cached = self._cache.get(text)
        if cached is None:
            cached, _ = parse(text, self.context)
            if len(self._cache) < _CACHE_ENTRIES:
                self._cache[text] = cached
        return cached
