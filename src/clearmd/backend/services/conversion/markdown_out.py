r"""Markdown that never does what the document did not write (ADR-0023, ADR-0024).

Shared by ClearMD's own converters. Document text is escaped on every path that copies it (never
a link, an image, a code span or raw HTML); ClearMD marks the block lines it writes itself with
``MARK``, and ``neutralize`` turns every other line a viewer would read as a block into plain
text, then removes the marks; pieces written next to each other are joined so they never form a
construct none of them wrote.
"""

import re
from collections.abc import Callable

MARK = "\ue000"  # starts each block line ClearMD writes itself; stripped from every input
# Before ASCII punctuation, or at the end of a piece (the next piece may start with some).
_ESCAPING_BACKSLASH = re.compile(r"\\(?=[!-/:-@\[-`{-~]|$)")

# ClearMD marks the start of every block line it writes itself (headings, list markers, quotes,
# fences, math, table rows, footnotes); a final pass neutralizes any other line that Markdown
# would read as a block, and removes the marks. The mark is stripped from the input first, so a
# document cannot forge it (ADR-0023).
_FENCE_LINE = re.compile(r"[ \t]*" + MARK + r"(`{3,}|~{3,})(.*)")


_OWN_FENCE = re.compile(r"(`{3,}|~{3,})(.*)")


ENTITY = re.compile(r"&[#A-Za-z]")


# What Markdown reads as a block at the start of a line written by the document.
_BLOCK_LINE = re.compile(
    r"(?P<mark>#{1,6}(?=\s|$)|>|[-+*](?=\s|$)|(?P<number>\d{1,9})(?=[.)](?:\s|$))"
    r"|`{3,}|~{3,}|\||\[[^\]\n]*\]:|[=]+[ \t]*$|-{2,}[ \t]*$"
    r"|(?P<rule>[-*_])(?:[ \t]*(?P=rule)){2,}[ \t]*$)"
)


_TABLE_RULE = re.compile(r"\|?[ \t]*:?-+:?[ \t]*(\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*")


_MATH_TAG = re.compile(r"<(?=[A-Za-z/!?])")


# http, https, ftp, mailto, or a relative path (never "//host": that is remote).
SAFE_LINK = re.compile(r"^(?:https?|ftp|mailto):|^(?![/\\]{2})[^:]*$", re.IGNORECASE)


def block(text: str) -> str:
    return f"\n\n{text.strip(chr(10))}\n\n"


def fence_for(code: str) -> str:
    longest = max((len(run) for run in re.findall("`+", code)), default=0)
    return "`" * max(3, longest + 1)


def inline_code(code: str) -> str:
    # One line: a code span cannot cross a blank line (it would stay open and its content live),
    # and CommonMark shows its line breaks as spaces anyway.
    code = re.sub(r"[ \t]*\n\s*", " ", code)
    if "`" not in code:
        return f"`{code}`"
    ticks = "`" * (max(len(run) for run in re.findall("`+", code)) + 1)
    return f"{ticks} {code} {ticks}"


def indent(text: str, width: int) -> str:
    lines = text.split("\n")
    return "\n".join([lines[0], *[(" " * width + line) if line else "" for line in lines[1:]]])


def outside_code(text: str, fix: Callable[[str], str], *, blank_around: bool = False) -> str:
    """``fix`` applied to the text between fenced code blocks; the blocks stay as they are.

    A line scanner (linear): a fence closes on a line of the same character, at least as long,
    with nothing else on it (CommonMark); an unclosed fence runs to the end.
    """
    pieces: list[tuple[bool, list[str]]] = [(False, [])]
    fence: str | None = None
    for line in text.split("\n"):
        found = _FENCE_LINE.fullmatch(line)
        if (
            fence is None
            and found is not None
            and not (found.group(1)[0] == "`" and "`" in found.group(2))
        ):
            fence = found.group(1)
            pieces.append((True, [line]))
        elif fence is not None:
            pieces[-1][1].append(line)
            run = found.group(1) if found is not None and not found.group(2).strip() else ""
            if run and run[0] == fence[0] and len(run) >= len(fence):
                fence = None
                pieces.append((False, []))
        else:
            pieces[-1][1].append(line)
    if not blank_around:
        return "\n".join(
            "\n".join(lines) if is_code else fix("\n".join(lines)) for is_code, lines in pieces
        )
    # Exactly one blank line between a code block and the text around it.
    parts = [
        "\n".join(lines) if is_code else fix("\n".join(lines)).strip("\n")
        for is_code, lines in pieces
    ]
    return "\n\n".join(part for part in parts if part)


def escape_text(text: str) -> str:
    """Text from the document never becomes a link, an image, a code span or raw HTML (blocks:
    neutralize; neighbours: ``join_pieces``)."""
    # The backslash first: a document's own "\\" before a backtick (or any ASCII punctuation, the
    # only characters CommonMark lets a backslash escape) must not cancel an escape. Elsewhere it
    # stays single, so "\\section" reads as written.
    text = _ESCAPING_BACKSLASH.sub(r"\\\\", text.replace(MARK, "")).replace("`", "\\`")
    # The document's own *, _ and ~ are characters, never emphasis or strike-through.
    text = text.replace("*", "\\*").replace("_", "\\_").replace("~", "\\~")
    return text.replace("<", "&lt;").replace("[", "&#91;").replace("]", "&#93;")


def escape_math(text: str) -> str:
    """Math is Markdown text to a viewer without math support. TeX ignores spaces in math, so
    ``< img``, ``! [`` and ``] (`` are the same formula and no HTML, image or link. A backtick
    would pair with one of ClearMD's code spans: it is escaped (rare in math)."""
    text = _MATH_TAG.sub("< ", text.replace(MARK, ""))
    text = text.replace("![", "! [").replace("](", "] (")
    # Not "\\`": in math a document's backslash before it would cancel the escape; an entity is
    # never a code delimiter (rare in math, shown as written by a math-aware viewer).
    return text.replace("`", "&#96;")


def join_pieces(parts: list[str]) -> str:
    """Pieces written next to each other never form a construct none of them wrote: a ``!``
    before ClearMD's ``[`` (an image), a ``]`` before ``(``, ``[`` or ``:`` (a link, a
    reference, a definition), two backtick runs glued into one (code spans that never close)."""
    pieces = [part for part in parts if part]
    for index in range(1, len(pieces)):
        left, right = pieces[index - 1], pieces[index]
        if left.endswith("!") and right.startswith("[") and not left.endswith("\\!"):
            pieces[index - 1] = left[:-1] + "\\!"
        elif left.endswith("]") and right.startswith(("(", "[", ":")):
            pieces[index] = "\\" + right
        elif left.endswith("`") and right.startswith("`"):  # two code spans, never one run
            pieces[index] = " " + right
    return "".join(pieces)


def math_line(line: str) -> str:
    """A display-math line a viewer without math would read as a block gets a ``{}`` (no-op)."""
    return "{}" + line if _neutral_line(line, after_blank=True) != line else line


def marked(text: str) -> str:
    """``text``'s lines, each marked as written by ClearMD."""
    return "\n".join(MARK + line for line in text.split("\n"))


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
    out: list[str] = []
    fence: str | None = None
    after_blank = True
    for line in text.split("\n"):
        stripped = line.lstrip(" \t")
        if stripped.startswith(MARK):
            own = _OWN_FENCE.match(stripped[1:])
            if fence is None and own is not None:
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


def link_target(path: str) -> str:
    """A Markdown link destination that stays one destination whatever ``path`` holds."""
    if not re.search(r"[\s()<>]", path):
        return path
    return "<" + path.replace("<", "%3C").replace(">", "%3E") + ">"


def ends_a_line(parts: list[str]) -> bool:
    for part in reversed(parts):
        if part:
            return part.endswith("\n")
    return False


def tidy(text: str) -> str:
    def tidy(part: str) -> str:
        # Trailing spaces go, except a hard line break ("  ") after real text.
        lines = [
            line if line.endswith("  ") and line.strip() else line.rstrip()
            for line in part.split("\n")
        ]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines))

    return outside_code(text, tidy, blank_around=True).strip() + "\n"
