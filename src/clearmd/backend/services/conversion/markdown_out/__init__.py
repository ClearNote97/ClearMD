r"""Markdown that never does what the document did not write (ADR-0023, ADR-0024).

Shared by ClearMD's own converters. Document text is escaped on every path that copies it (never
a link, an image, a code span or raw HTML); ClearMD marks the block lines it writes itself with
``MARK``, and ``neutralize`` turns every other line a viewer would read as a block into plain
text, then removes the marks; pieces written next to each other are joined so they never form a
construct none of them wrote.
"""

from clearmd.backend.services.conversion.markdown_out.code import (
    fence_for,
    inline_code,
    outside_code,
)
from clearmd.backend.services.conversion.markdown_out.escaping import (
    ENTITY,
    SAFE_LINK,
    escape_math,
    escape_text,
    heading_text,
    join_pieces,
    link_target,
)
from clearmd.backend.services.conversion.markdown_out.marks import (
    MARK,
    block,
    ends_a_line,
    indent,
    indent_all,
    line_endings,
    marked,
    own_line,
    starts_tight,
    starts_with_fence,
)
from clearmd.backend.services.conversion.markdown_out.neutralize import math_line, neutralize, tidy

__all__ = [
    "ENTITY",
    "MARK",
    "SAFE_LINK",
    "block",
    "ends_a_line",
    "escape_math",
    "escape_text",
    "fence_for",
    "heading_text",
    "indent",
    "indent_all",
    "inline_code",
    "join_pieces",
    "line_endings",
    "link_target",
    "marked",
    "math_line",
    "neutralize",
    "outside_code",
    "own_line",
    "starts_tight",
    "starts_with_fence",
    "tidy",
]
