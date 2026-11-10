"""The output guarantee for every converter, ClearMD's own or a third party's (audit v3, B2-01):
opening a result never fetches anything nor runs anything.

- An image with a web address, a network share (UNC) or an absolute path becomes its text
  (``[image: alt]``): a remote picture is a read receipt for whoever sent the document. Relative
  images (the result's own image folder, ADR-0033) and inline ``data:`` images stay.
- A link to ``file:``, ``javascript:``, ``vbscript:``, ``data:`` or a network share keeps only its
  text. Web links stay: following them is the reader's choice.
- Raw HTML that can fetch or run (``<img>``, ``<script>``, ``<iframe>``… or any ``on…=``
  attribute) is escaped, so a viewer shows it as text.

Fenced code and code spans are left alone.
"""

import html
import re

from clearmd.backend.services.conversion.markdown_out.code import outside_code

# A link's target: up to its closing parenthesis, one level of balanced ones inside (CommonMark):
# "javascript:alert(1)" is one target, not "javascript:alert(1" and a stray ")".
_TARGET = r"\(\s*<?((?:[^()\s>]|\([^()\s]*\))*)>?(?:\s+(?:\"[^\"\n]*\"|'[^'\n]*'))?\s*\)"
_IMAGE = re.compile(r"!\[([^\]\n]*)\]" + _TARGET)
_LINK = re.compile(r"(?<!!)\[([^\]\n]*)\]" + _TARGET)
# The only pictures that stay: a relative path (the result's folders, ADR-0033, or the
# original's, from a TeX document), or an inline picture. Anything else that could be read as
# a picture is written as text (audit v4).
_OWN_PICTURE = re.compile(r"(?![/\\])[^:\s<>\\]+")  # relative, ".." too: a local file
_UNSAFE_LINK = re.compile(r"\s*(?:file|javascript|vbscript|data):|\\\\", re.IGNORECASE)
# A reference definition ("[r]: target") to a place a link must never lead.
_DEFINITION = re.compile(r"^( {0,3})\[([^\]\n]+)\]:[ \t]*<?([^\s>]+)", re.MULTILINE)
_ACTIVE_HTML = re.compile(
    r"<(?=/?(?:img|script|iframe|frame|object|embed|svg|math|style|link|meta|base|form|input"
    r"|button|video|audio|source|track|picture|image)\b"
    r"|[A-Za-z][\w-]*\s[^>\n]*=)",  # any tag with an attribute: src, href, style, on…
    re.IGNORECASE,
)
_CODE_SPAN = re.compile(r"(`+)(?:.*?[^`])?\1(?!`)", re.DOTALL)


def _own(address: str) -> bool:
    address = html.unescape(address)
    return address.lower().startswith("data:image/") or bool(_OWN_PICTURE.fullmatch(address))


def _pictures(text: str) -> tuple[str, int]:
    """Every "![" either opens a picture of the result's own, or is written as text: one regular
    expression cannot follow every way Markdown has to write a picture (nested brackets,
    references, entities, a text over two lines), so whatever is not plainly safe is text."""
    out: list[str] = []
    changed = 0
    last = 0
    for start in (m.start() for m in re.finditer(r"!\[", text)):
        if start < last:
            continue
        found = _IMAGE.match(text, start)
        out.append(text[last:start])
        if found is not None and _own(found.group(2)):
            out.append(found.group(0))
            last = found.end()
            continue
        changed += 1
        if found is not None:
            alt = found.group(1).strip()
            out.append(f"[image: {alt}]" if alt else "[image]")
            last = found.end()
        else:
            out.append("!\\[")
            last = start + 2
    out.append(text[last:])
    return "".join(out), changed


def _unsafe(address: str) -> bool:
    return bool(_UNSAFE_LINK.match(html.unescape(address)))


def _outside_spans(line_block: str) -> tuple[str, int]:
    out: list[str] = []
    changed = 0
    last = 0
    for span in _CODE_SPAN.finditer(line_block):
        piece, count = _safe_prose(line_block[last : span.start()])
        out += [piece, span.group(0)]
        changed += count
        last = span.end()
    piece, count = _safe_prose(line_block[last:])
    return "".join([*out, piece]), changed + count


def _safe_prose(text: str) -> tuple[str, int]:
    text, changed = _pictures(text)
    count = [changed]

    def link(found: re.Match[str]) -> str:
        if not _unsafe(found.group(2)):
            return found.group(0)
        count[0] += 1
        return found.group(1)

    def definition(found: re.Match[str]) -> str:
        if not _unsafe(found.group(3)):
            return found.group(0)
        count[0] += 1
        return found.group(1) + "\\" + found.group(0)[len(found.group(1)) :]

    text = _DEFINITION.sub(definition, _LINK.sub(link, text))
    text, tags = _ACTIVE_HTML.subn("&lt;", text)
    return text, count[0] + tags


def safe_output(markdown: str) -> tuple[str, int]:
    """``markdown`` with nothing that fetches or runs when opened, and how many things changed."""
    changed = 0

    def fix(text: str) -> str:
        nonlocal changed
        fixed, count = _outside_spans(text)
        changed += count
        return fixed

    return outside_code(markdown, fix), changed
