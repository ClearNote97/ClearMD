"""A Markdown file cut at its headings (feature 024, ADR-0045). Text in, parts out.

Nothing inside changes: the parts, put back together, are the file byte for byte. Cuts fall
only between blocks (paragraphs, lists, tables, fenced code), never inside a code fence. A
section larger than the size is cut at its paragraphs; a block larger than the size is a part
alone.
"""

import re
from dataclasses import dataclass

from clearmd.backend.schemas.split import Cut
from clearmd.backend.services.split.words import count_words

_FENCE = re.compile(r"^ {0,3}(```|~~~)")
_HEADING = re.compile(r"^ {0,3}#{1,6}(\s|$)")


@dataclass(frozen=True)
class _Block:
    text: str
    words: int
    heading: bool


def _blocks(text: str) -> list[_Block]:
    raw: list[list[str]] = []
    current: list[str] = []
    fenced = blank_before = False
    for line in text.splitlines(keepends=True):
        content = line.strip()
        if not fenced and current and ((blank_before and content) or _HEADING.match(line)):
            raw.append(current)
            current = []
        current.append(line)
        if _FENCE.match(line):
            fenced = not fenced
        blank_before = not fenced and not content
    if current:
        raw.append(current)
    blocks = []
    for lines in raw:
        joined = "".join(lines)
        blocks.append(_Block(joined, count_words(joined), bool(_HEADING.match(lines[0]))))
    return blocks


def _sections(blocks: list[_Block]) -> list[list[_Block]]:
    sections: list[list[_Block]] = []
    for block in blocks:
        if block.heading or not sections:
            sections.append([])
        sections[-1].append(block)
    return sections


def _by_words(blocks: list[_Block], size: int) -> list[list[_Block]]:
    """Whole sections up to ``size`` words; a larger section by its blocks; a larger block alone."""
    units: list[list[_Block]] = []
    for section in _sections(blocks):
        if sum(block.words for block in section) <= size:
            units.append(section)
        else:
            units.extend([block] for block in section)
    parts: list[list[_Block]] = []
    total = 0
    for unit in units:
        words = sum(block.words for block in unit)
        if parts and total + words <= size:
            parts[-1].extend(unit)
            total += words
        else:
            parts.append(list(unit))
            total = words
    return parts


def _into(blocks: list[_Block], count: int) -> list[list[_Block]]:
    """``count`` parts as even as possible by words, cut at headings (at blocks when there are
    too few headings); never an empty part."""
    sections = _sections(blocks)
    units = sections if len(sections) >= count else [[block] for block in blocks]
    weights = [max(1, sum(block.words for block in unit)) for unit in units]
    total = sum(weights)
    cuts: list[int] = []
    reached = 0
    for index, weight in enumerate(weights[:-1], start=1):
        reached += weight
        target = total * (len(cuts) + 1) / count
        if len(cuts) < count - 1 and reached >= target - weight / 2:
            cuts.append(index)
    bounds = [0, *cuts, len(units)]
    return [
        [block for unit in units[start:end] for block in unit]
        for start, end in zip(bounds, bounds[1:], strict=False)
        if end > start
    ]


def cut_markdown(text: str, cut: Cut, size: int) -> tuple[tuple[str, ...], tuple[int, ...]]:
    """The parts, and which parts (1-based) are larger than ``size`` words (cut by words)."""
    blocks = _blocks(text)
    if not blocks:
        return (), ()
    if cut is Cut.WORDS:
        groups = _by_words(blocks, size)
    elif cut is Cut.PARTS:
        groups = _into(blocks, size)
    else:
        raise ValueError(f"{cut.value} does not apply to Markdown")
    parts = tuple("".join(block.text for block in group) for group in groups)
    over = tuple(
        number
        for number, group in enumerate(groups, start=1)
        if cut is Cut.WORDS and sum(block.words for block in group) > size
    )
    return parts, over
