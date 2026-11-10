"""Document text made safe: escaped text and math, pieces joined, link targets, heading text."""

import re

from clearmd.backend.services.conversion.markdown_out.marks import MARK

# Before ASCII punctuation, or at the end of a piece (the next piece may start with some).
_ESCAPING_BACKSLASH = re.compile(r"\\(?=[!-/:-@\[-`{-~]|$)")


ENTITY = re.compile(r"&[#A-Za-z]")
# Only an "&" that a viewer would read as an entity ("&copy;", or "&copy" at a piece's end, which
# the next piece could close): "AT&T" stays as it is (audit v4, B3-06).
_ENTITY_START = re.compile(r"&(?=#?\w+(?:;|$))")
_EDGE_UNDERSCORE = re.compile(r"(?<![A-Za-z0-9\u00C0-\u024F])_|_(?![A-Za-z0-9\u00C0-\u024F])")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_ESCAPED_BANG = re.compile(r"(?<!\\)(?:\\\\)*\\!$")  # an odd run of backslashes before it


_MATH_TAG = re.compile(r"<(?=[A-Za-z/!?])")


# http, https, ftp, mailto, or a relative path (never "//host": that is remote).
SAFE_LINK = re.compile(r"^(?:https?|ftp|mailto):|^(?![/\\]{2})[^:]*$", re.IGNORECASE)


def heading_text(text: str) -> str:
    """A heading's text whose final "#" is never read as the optional closing sequence."""
    return text[:-1] + "\\#" if text.endswith("#") and not text.endswith("\\#") else text


def escape_text(text: str) -> str:
    """Text from the document never becomes a link, an image, a code span or raw HTML (blocks:
    neutralize; neighbours: ``join_pieces``)."""
    # The backslash first: a document's own "\\" before a backtick (or any ASCII punctuation, the
    # only characters CommonMark lets a backslash escape) must not cancel an escape. Elsewhere it
    # stays single, so "\\section" reads as written.
    text = _ESCAPING_BACKSLASH.sub(r"\\\\", text.replace(MARK, "")).replace("`", "\\`")
    # An entity the document wrote ("&lt;", "&copy;") shows as written, never decoded.
    text = _ENTITY_START.sub("&amp;", text)
    # The document's own *, _ and ~ are characters, never emphasis or strike-through. An "_"
    # inside a word is never emphasis (CommonMark): "juan_perez" stays readable (doubts board 2).
    text = text.replace("*", "\\*").replace("~", "\\~")
    text = _EDGE_UNDERSCORE.sub("\\_", text)
    # Readable marks an AI reads as text: "\[", not "&#91;" (audit v4, B3-06; ADR-0023 amended).
    return text.replace("<", "&lt;").replace("[", "\\[").replace("]", "\\]")


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
    before ClearMD's ``[`` (an image), a ``]`` before ``(`` or ``:`` (a link, a definition),
    two backtick runs glued into one (code spans that never close). A ``]`` before ``[`` stays:
    the document's brackets are always escaped ("\\["), so an unescaped pair is ClearMD's
    (``[^1][t](u)`` is a footnote and a link, ``[^1][^2]`` two references)."""
    pieces = [part for part in parts if part]
    for index in range(1, len(pieces)):
        left, right = pieces[index - 1], pieces[index]
        # Escaped only after an odd run of backslashes: "\\\\!" is a backslash and a live "!".
        if left.endswith("!") and right.startswith("[") and not _ESCAPED_BANG.search(left):
            pieces[index - 1] = left[:-1] + "\\!"
        elif left.endswith("]") and right.startswith(("(", ":")):
            pieces[index] = "\\" + right
        elif left.endswith("`") and right.startswith("`"):  # two code spans, never one run
            pieces[index] = " " + right
    return "".join(pieces)


def link_target(path: str) -> str:
    """A Markdown link destination that stays one destination whatever ``path`` holds. A
    backtick or a backslash is encoded: a code span takes precedence over a link, and a
    backslash would escape what follows."""
    path = path.replace("\\", "%5C").replace("`", "%60")
    # "&" as a character: a query string stays one (?a=1&b=2), and no entity is ever decoded in
    # it ("javascript&colon;" stays a harmless relative path).
    path = path.replace("&", "\\&")
    # A control character (a line break above all) would end the destination: "<x\nonclick=…>"
    # is then an HTML tag. Encoded, it is one more character of the address.
    path = _CONTROL.sub(lambda found: f"%{ord(found.group()):02X}", path)
    if not re.search(r"[\s()<>]", path):
        return path
    return "<" + path.replace("<", "%3C").replace(">", "%3E") + ">"
