r"""The author's own macros: collected in document order, expanded with a budget (ADR-0022).

Expanded: ``\newcommand``/``\renewcommand``/``\providecommand`` (up to 9 arguments, an optional
first one with its default), ``\DeclareMathOperator`` and ``\def`` without parameters. ``#1`` …
``#9`` are replaced in one pass (what an argument brings is never replaced again; ``##`` is
``#``), and the size of an expansion is charged to the budget before the text is built, so a macro
bomb (recursive, exponential or wide) hits the budget, stops expanding, and is reported.
"""

from clearmd.backend.services.conversion.tex.macros.collect import (
    DefinitionSite,
    collect_definitions,
    definition_sites,
    is_parametrized_def,
)
from clearmd.backend.services.conversion.tex.macros.definition import (
    MacroDefinition,
    opens_or_closes_an_environment,
)
from clearmd.backend.services.conversion.tex.macros.expander import (
    BudgetExceeded,
    MacroExpander,
    build_expander,
    expansion_limit,
)
from clearmd.backend.services.conversion.tex.macros.substitution import substitute_structural

__all__ = [
    "BudgetExceeded",
    "DefinitionSite",
    "MacroDefinition",
    "MacroExpander",
    "build_expander",
    "collect_definitions",
    "definition_sites",
    "expansion_limit",
    "is_parametrized_def",
    "opens_or_closes_an_environment",
    "substitute_structural",
]
