"""The shape of a document: preamble and body, the shallowest sectioning used, the language."""

import re
from typing import Any

from pylatexenc.latexwalker import LatexEnvironmentNode, LatexMacroNode

from clearmd.backend.services.conversion.tex.macros import MacroDefinition
from clearmd.backend.services.conversion.tex.nodes import argument, is_macro, raw, walk
from clearmd.backend.services.conversion.tex.writer.vocab import LANGUAGES, SECTION_LEVELS

_SECTIONING_IN_BODY = re.compile(r"\\(" + "|".join(SECTION_LEVELS) + r")(?![A-Za-z@])")


def split_document(nodes: list[Any]) -> tuple[list[Any], list[Any]]:
    """The preamble and the body (everything, when there is no ``document`` environment)."""
    for index, node in enumerate(nodes):
        if isinstance(node, LatexEnvironmentNode) and node.environmentname == "document":
            return nodes[:index], list(node.nodelist or [])
    return nodes, nodes


def top_level(nodes: list[Any], definitions: dict[str, MacroDefinition] | None = None) -> int:
    """The shallowest sectioning command really used (comments and code are separate nodes),
    also inside the author's macros that are used (``\\mychap`` → ``\\chapter``)."""
    _, body = split_document(nodes)
    used: set[str] = set()
    present = []
    for node in walk(body):
        if isinstance(node, LatexMacroNode):
            if node.macroname in SECTION_LEVELS:
                present.append(SECTION_LEVELS[node.macroname])
            elif definitions and node.macroname in definitions:
                used.add(node.macroname)
    for name in used:
        assert definitions is not None
        present.extend(
            SECTION_LEVELS[n] for n in _SECTIONING_IN_BODY.findall(definitions[name].body)
        )
    return min(present, default=SECTION_LEVELS["section"])


def _options(node: Any, index: int) -> list[str]:
    return [option.strip() for option in raw(argument(node, index)).split(",") if option.strip()]


def is_spanish(nodes: list[Any]) -> bool:
    """babel's main language (its last option, else the class's) or polyglossia's is Spanish."""
    preamble, _ = split_document(nodes)
    babel: list[str] = []
    global_options: list[str] = []
    main = ""
    for node in walk(preamble):
        if is_macro(node, "usepackage") and "babel" in _options(node, 1):
            babel = _options(node, 0) or babel
            chosen = [o.split("=", 1)[1] for o in babel if o.replace(" ", "").startswith("main=")]
            main = chosen[-1].strip() if chosen else main
        elif is_macro(node, "documentclass"):
            global_options = _options(node, 0)
        elif is_macro(node, "setmainlanguage") or is_macro(node, "setdefaultlanguage"):
            main = raw(argument(node, -1)).strip()
    if not main and babel:
        main = babel[-1]
    elif not main:
        languages = [o for o in global_options if o.lower() in LANGUAGES]
        main = languages[-1] if languages else ""
    return main.lower().startswith(("spanish", "español"))
