"""The mark ClearMD puts on the block lines it writes itself, and the small line helpers around it.

Stands at the bottom of the package: every other module reads ``MARK`` and the fence patterns.
"""

import re

MARK = "\ue000"  # starts each block line ClearMD writes itself; stripped from every input


# ClearMD marks the start of every block line it writes itself (headings, list markers, quotes,
# fences, math, table rows, footnotes); a final pass neutralizes any other line that Markdown
# would read as a block, and removes the marks. The mark is stripped from the input first, so a
# document cannot forge it (ADR-0023).
FENCE_LINE = re.compile(r"[ \t]*" + MARK + r"(`{3,}|~{3,})(.*)")


OWN_FENCE = re.compile(r"(`{3,}|~{3,})(.*)")
BARE_MARKER = re.compile(r"[ \t]*" + MARK + r"(?:[-*+]|\d{1,9}[.)])")  # a list marker alone


def block(text: str) -> str:
    return f"\n\n{text.strip(chr(10))}\n\n"


def starts_with_fence(content: str) -> bool:
    """Whether a list item's content opens with a code fence: the marker then goes on its own
    line ("-" and the fence below), because ``neutralize`` and ``outside_code`` read a fence at
    the start of a line only, and one after "- " would be missed (verification of 004)."""
    first = content.split("\n", 1)[0].lstrip(" \t").lstrip(MARK)
    return OWN_FENCE.match(first) is not None


def indent(text: str, width: int) -> str:
    lines = text.split("\n")
    return "\n".join([lines[0], *[(" " * width + line) if line else "" for line in lines[1:]]])


def opens_fence(found: re.Match[str]) -> bool:
    """CommonMark: a backtick fence's info string never holds a backtick (that line is an inline
    code span, as ``inline_code`` writes one)."""
    return not (found.group(1)[0] == "`" and "`" in found.group(2))


def starts_tight(part: str) -> bool:
    """A nested list Markdown lets follow a paragraph directly: bullets, or numbers from 1."""
    return re.match(rf"{MARK}(?:[-*] |1[.)] )", part) is not None


def own_line(line: str) -> str:
    """``line`` marked as ClearMD's, after its indentation (where ``outside_code`` looks)."""
    content = line.lstrip(" \t")
    if not content or content.startswith(MARK):
        return line
    return line[: len(line) - len(content)] + MARK + content


def indent_all(text: str, width: int) -> str:
    """Every non-empty line of ``text`` indented by ``width`` (``indent`` skips the first)."""
    return "\n".join(" " * width + line if line else "" for line in text.split("\n"))


def marked(text: str) -> str:
    """``text``'s lines, each marked as written by ClearMD."""
    return "\n".join(MARK + line for line in text.split("\n"))


def line_endings(text: str) -> str:
    """CommonMark ends a line at "\n", "\r" or "\r\n": everything here splits on "\n" only."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def ends_a_line(parts: list[str]) -> bool:
    for part in reversed(parts):
        if part:
            return part.endswith("\n")
    return False
