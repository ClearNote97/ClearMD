r"""Text substitution of the macros that open or close an environment (``\beq``)."""

import bisect
import re
from collections.abc import Callable
from typing import Any

from clearmd.backend.services.conversion.tex.macros.collect import DefinitionSite, definition_sites
from clearmd.backend.services.conversion.tex.macros.definition import opens_or_closes_an_environment
from clearmd.backend.services.conversion.tex.macros.expander import BudgetExceeded, MacroExpander
from clearmd.backend.services.conversion.tex.parsing import make_context, mask, parse

MAX_SUBSTITUTION_ROUNDS = 4  # \\myeq → \\bal → \\begin{align}: chains are short


def _substitute_round(
    text: str, nodes: list[Any], macros: MacroExpander
) -> tuple[str, list[tuple[int, int, int, int]]] | None:
    """One round of text substitution of structural macros, in document order (each use takes
    the definition in force where it is written). ``None`` when there is nothing to do."""
    sites = definition_sites(nodes)
    structural = {
        site.name
        for site in sites
        if site.name and site.definition and opens_or_closes_an_environment(site.definition)
    }
    if not structural:
        return None
    by_name: dict[str, list[DefinitionSite]] = {}
    for site in sites:
        if site.name in structural:
            by_name.setdefault(site.name, []).append(site)
    heads = sorted((site.head_start, site.head_end) for site in sites)
    head_starts = [start for start, _ in heads]
    names = "|".join(re.escape(name) for name in sorted(structural, key=len, reverse=True))
    use = re.compile(r"\\(" + names + r")(?![A-Za-z@])")
    pieces: list[str] = []
    moved: list[tuple[int, int, int, int]] = []  # new start, new end, old start, old end
    cursor = length = 0
    for found in use.finditer(mask(text)):
        at = bisect.bisect_right(head_starts, found.start()) - 1
        if at >= 0 and found.start() < heads[at][1]:
            continue  # the name being defined, never a use
        defined = [site for site in by_name[found.group(1)] if site.head_start < found.start()]
        definition = defined[-1].definition if defined else None
        if definition is None or not opens_or_closes_an_environment(definition):
            continue
        try:
            macros.charge(found.group(1), len(definition.body))
        except BudgetExceeded:
            break
        before = text[cursor : found.start()]
        pieces.append(before)
        length += len(before)
        replacement = definition.body + " "
        moved.append((length, length + len(replacement), found.start(), found.end()))
        pieces.append(replacement)
        length += len(replacement)
        cursor = found.end()
    if not moved:
        return None
    pieces.append(text[cursor:])
    return "".join(pieces), moved


def substitute_structural(
    text: str, nodes: list[Any], macros: MacroExpander
) -> tuple[str, list[Any], Callable[[int], int]] | None:
    r"""Uses of ``\beq`` → ``\begin{equation}`` in the text itself, as TeX does, so that the
    environment they open takes the text up to the macro that closes it. Repeated while a round
    makes new uses appear (``\myeq`` → ``\bal`` → ``\begin{align}``, or inside a body); never
    inside a definition's head, a comment or code; charged to the budget like any expansion."""
    rounds: list[list[tuple[int, int, int, int]]] = []
    for _ in range(MAX_SUBSTITUTION_ROUNDS):
        done = _substitute_round(text, nodes, macros)
        if done is None:
            break
        text, moved = done
        rounds.append(moved)
        nodes, _ = parse(text, make_context())
    if not rounds:
        return None

    def original(position: int) -> int:
        for moved in reversed(rounds):
            index = bisect.bisect_right([m[0] for m in moved], position) - 1
            if index < 0:
                continue
            new_start, new_end, old_start, old_end = moved[index]
            position = old_start if position < new_end else old_end + (position - new_end)
        return position

    return text, nodes, original
