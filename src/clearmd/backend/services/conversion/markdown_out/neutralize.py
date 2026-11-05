"""The final pass: every line the document wrote that Markdown would read as a block becomes plain
text, and ``tidy`` cleans the result. ``tidy`` shares the module: it is the pass that follows.
"""

import re

from clearmd.backend.services.conversion.markdown_out.code import outside_code
from clearmd.backend.services.conversion.markdown_out.marks import (
    MARK,
    OWN_FENCE,
    line_endings,
    opens_fence,
)

# What Markdown reads as a block at the start of a line written by the document.
_BLOCK_LINE = re.compile(
    r"(?P<mark>#{1,6}(?=\s|$)|>|[-+*](?=\s|$)|(?P<number>\d{1,9})(?=[.)](?:\s|$))"
    r"|`{3,}|~{3,}|\||\[[^\]\n]*\]:|[=]+[ \t]*$|-{2,}[ \t]*$"
    r"|(?P<rule>[-*_])(?:[ \t]*(?P=rule)){2,}[ \t]*$)"
)


_TABLE_RULE = re.compile(r"\|?[ \t]*:?-+:?[ \t]*(\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*")


def math_line(line: str) -> str:
    """A display-math line a viewer without math would read as a block gets a ``{}`` (no-op)."""
    return "{}" + line if _neutral_line(line, after_blank=True) != line else line


def _neutral_line(line: str, after_blank: bool) -> str:
    indent = len(line) - len(line.lstrip(" \t"))
    content = line[indent:]
    columns = len(line[:indent].expandtabs(4))  # a tab is up to 4 columns to CommonMark
    if after_blank and columns >= 4:  # an indented code block
        indent, columns, line = 0, 0, content
    if columns >= 4 or not content:
        return line
    if _TABLE_RULE.fullmatch(content) and "|" in content:
        return line[:indent] + "\\" + content
    found = _BLOCK_LINE.match(content)
    if found is None:
        return line
    run = len(content) - len(content.lstrip("`"))
    if run >= 3 and "`" in content[run:]:
        return line  # not a fence (CommonMark): an inline code span at the start of the line
    if found.group("number") is not None:
        digits = found.group("number")
        return line[:indent] + digits + "\\" + content[len(digits) :]
    if content[0] == "<":
        return line[:indent] + "&lt;" + content[1:]
    return line[:indent] + "\\" + content


def neutralize(text: str, *, keep_marks: bool = False) -> str:
    """Every line the document wrote that Markdown would read as a block becomes plain text;
    ClearMD's own marked lines (and the code inside its fences) stay; the marks go (or stay,
    for a part that is marked again as a whole: a list item, a quote)."""
    text = line_endings(text)
    out: list[str] = []
    fence: str | None = None
    after_blank = True
    for line in text.split("\n"):
        stripped = line.lstrip(" \t")
        if stripped.startswith(MARK):
            own = OWN_FENCE.match(stripped[1:])
            if fence is None and own is not None and opens_fence(own):
                fence = own.group(1)
            elif fence is not None and own is not None and not own.group(2).strip():
                if own.group(1)[0] == fence[0] and len(own.group(1)) >= len(fence):
                    fence = None
            out.append(line if keep_marks else line.replace(MARK, ""))
        elif fence is not None:
            out.append(line)  # code, as written
        else:
            out.append(_neutral_line(line, after_blank))
        after_blank = not line.strip()
    joined = "\n".join(out)
    return joined if keep_marks else joined.replace(MARK, "")


def tidy(text: str) -> str:
    text = line_endings(text)

    def tidy(part: str) -> str:
        # Trailing spaces go, except a hard line break ("  ") after real text.
        lines = [
            line if line.endswith("  ") and line.strip() else line.rstrip()
            for line in part.split("\n")
        ]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines))

    return outside_code(text, tidy, blank_around=True).strip() + "\n"
