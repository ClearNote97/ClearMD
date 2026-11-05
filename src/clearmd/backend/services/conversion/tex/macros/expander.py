"""Expanding the author's macros within a budget (expansions, growth, nesting)."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from pylatexenc.macrospec import MacroSpec

from clearmd.backend.schemas.notes import NoteReason
from clearmd.backend.services.conversion.tex.macros.collect import collect_definitions, inner
from clearmd.backend.services.conversion.tex.macros.definition import MacroDefinition
from clearmd.backend.services.conversion.tex.parsing import make_context, parse

MAX_EXPANSIONS = 10_000  # at least; 10 per KiB of source for larger documents
EXPANSIONS_PER_KIB = 10
MAX_NESTING = 64
GROWTH_FACTOR = 4
GROWTH_EXTRA = 1024**2
_CACHE_ENTRIES = 4096


def expansion_limit(source_size: int) -> int:
    """10,000 expansions, or 10 per KiB of source when that is more (a 1 MiB thesis that uses
    ``\\R`` in every equation needs more than 10,000; growth and nesting still stop bombs)."""
    return max(MAX_EXPANSIONS, EXPANSIONS_PER_KIB * source_size // 1024)


class BudgetExceeded(Exception):
    def __init__(self, reason: NoteReason) -> None:
        super().__init__(reason.value)
        self.reason = reason


class MacroExpander:
    def __init__(self, definitions: dict[str, MacroDefinition], source_size: int) -> None:
        self.definitions = definitions
        specs = [MacroSpec(name, d.argspec) for name, d in definitions.items()]
        self.context = make_context(specs)
        self.limit_growth = GROWTH_FACTOR * source_size + GROWTH_EXTRA
        self.max_expansions = expansion_limit(source_size)
        self.expansions = 0
        self.produced = 0
        self.depth = 0
        self.exhausted: NoteReason | None = None
        self.limited: str | None = None  # the top-level use that hit the budget first
        self._cache: dict[str, list[Any]] = {}

    def redefine(self, definitions: dict[str, MacroDefinition]) -> None:
        """New definitions (after text substitution), keeping the budget already spent."""
        self.definitions = definitions
        self.context = make_context([MacroSpec(n, d.argspec) for n, d in definitions.items()])
        self._cache.clear()

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

    def charge(self, name: str, size: int) -> None:
        """One expansion of ``size`` characters done outside the node tree (text substitution)."""
        if self.exhausted is not None:
            raise BudgetExceeded(self.exhausted)
        self.expansions += 1
        self.produced += size
        if self.expansions > self.max_expansions:
            self.limited = self.limited or f"\\{name}"
            self._exceed(NoteReason.EXPANSIONS)
        if self.produced > self.limit_growth:
            self.limited = self.limited or f"\\{name}"
            self._exceed(NoteReason.GROWTH)

    def expand(self, node: Any) -> list[Any]:
        """The nodes a use of an author's macro stands for (charged to the budget first)."""
        if self.exhausted is not None:
            raise BudgetExceeded(self.exhausted)
        definition = self.definitions[node.macroname]
        arguments = getattr(getattr(node, "nodeargd", None), "argnlist", None) or []
        values = [inner(argument) if argument is not None else None for argument in arguments]
        if definition.default is not None and values and values[0] is None:
            values[0] = definition.default
        filled = [value or "" for value in values]
        self.expansions += 1
        if self.expansions > self.max_expansions:
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


def build_expander(nodes: list[Any], source_size: int) -> tuple[MacroExpander | None, bool]:
    """The author's macros, and whether the source must be parsed again with their arguments."""
    definitions = collect_definitions(nodes)
    if not definitions:
        return None, False
    base = make_context()
    again = any(
        definition.arguments or base.get_macro_spec(name) is not None
        for name, definition in definitions.items()
    )
    return MacroExpander(definitions, source_size), again
