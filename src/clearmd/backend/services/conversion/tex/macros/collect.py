"""Finding the author's definitions in the nodes, in document order, and where each is written."""

import re
from dataclasses import dataclass
from typing import Any

from pylatexenc.latexwalker import LatexGroupNode, LatexMacroNode

from clearmd.backend.services.conversion.tex.macros.definition import MacroDefinition

DEFINING = frozenset({"newcommand", "renewcommand", "providecommand"})


def inner(node: Any) -> str:
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
        count_text = inner(arguments[2]).strip()
        count = int(count_text) if re.fullmatch("[1-9]", count_text) else 0  # never "²"
        default = inner(arguments[3]) if arguments[3] is not None else None
        definition = MacroDefinition(name, count, default if count else None, inner(arguments[4]))
        if node.macroname == "providecommand" and name in found:
            return
        found[name] = definition
    elif node.macroname == "DeclareMathOperator" and len(arguments) == 3:
        name = _defined_name(arguments[1])
        if name is not None:
            star = "*" if arguments[0] is not None else ""
            body = f"\\operatorname{star}{{{inner(arguments[2])}}}"
            found[name] = MacroDefinition(name, 0, None, body)
    elif node.macroname == "def":
        parsed = getattr(node.nodeargd, "clearmd_def", None)
        if parsed is not None and not parsed.parameters.strip():
            found[parsed.name] = MacroDefinition(parsed.name, 0, None, parsed.body.chars)


DEFINITIONS = DEFINING | {"DeclareMathOperator", "def"}


@dataclass(frozen=True)
class DefinitionSite:
    """Where a definition is written: ``head`` (``\\newcommand{\\x}``) is never substituted
    into; its body is, so a macro built from a structural one works."""

    head_start: int
    head_end: int
    name: str | None
    definition: MacroDefinition | None


def definition_sites(nodes: list[Any]) -> list[DefinitionSite]:
    """Every definition, in document order, with the span of its head."""
    sites = []
    pending = list(reversed(nodes))
    while pending:
        node = pending.pop()
        if node is None:
            continue
        if isinstance(node, LatexMacroNode) and node.macroname in DEFINITIONS:
            found: dict[str, MacroDefinition] = {}
            _definition(node, found)
            name, definition = next(iter(found.items()), (None, None))
            body = _body_node(node)
            head_end = body.pos if body is not None else node.pos + node.len
            sites.append(DefinitionSite(node.pos, head_end, name, definition))
            continue
        pending.extend(reversed(_children(node)))
    return sites


def _body_node(node: Any) -> Any:
    parsed = getattr(getattr(node, "nodeargd", None), "clearmd_def", None)
    if parsed is not None:
        return parsed.body
    arguments = getattr(getattr(node, "nodeargd", None), "argnlist", None) or []
    return arguments[-1] if arguments else None


def is_parametrized_def(node: Any) -> bool:
    parsed = getattr(getattr(node, "nodeargd", None), "clearmd_def", None)
    return parsed is None or bool(parsed.parameters.strip())
