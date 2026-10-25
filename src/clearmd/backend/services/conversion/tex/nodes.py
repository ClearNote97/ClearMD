"""Walking pylatexenc node trees in document order, without recursion (deep input never crashes)."""

from collections.abc import Callable, Iterator
from typing import Any

from pylatexenc.latexwalker import LatexGroupNode, LatexMacroNode

# Marks the start of each block line ClearMD writes itself (see render.neutralize, ADR-0023).
MARK = "\ue000"


def children(node: Any) -> list[Any]:
    """A node's content and arguments, in source order."""
    arguments = getattr(getattr(node, "nodeargd", None), "argnlist", None) or []
    found = [*(getattr(node, "nodelist", None) or []), *(a for a in arguments if a is not None)]
    return sorted((n for n in found if n is not None), key=lambda n: n.pos or 0)


def walk(nodes: list[Any] | None, skip: Callable[[Any], bool] = lambda _: False) -> Iterator[Any]:
    """Every node under ``nodes``; a node for which ``skip`` is true is yielded, not entered."""
    pending = [node for node in reversed(nodes or []) if node is not None]
    while pending:
        node = pending.pop()
        yield node
        if not skip(node):
            pending.extend(reversed(children(node)))


def is_macro(node: Any, name: str) -> bool:
    return isinstance(node, LatexMacroNode) and node.macroname == name


def raw(node: Any) -> str:
    """The LaTeX source of an argument without its outer braces."""
    if node is None:
        return ""
    if isinstance(node, LatexGroupNode):
        return "".join(child.latex_verbatim() for child in node.nodelist or [])
    text: str = node.latex_verbatim()
    return text


def argument(node: Any, index: int) -> Any:
    arguments = getattr(getattr(node, "nodeargd", None), "argnlist", None) or []
    return arguments[index] if -len(arguments) <= index < len(arguments) else None
