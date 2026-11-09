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

import re

from clearmd.backend.services.conversion.markdown_out.code import outside_code

# A link's target: up to its closing parenthesis, one level of balanced ones inside (CommonMark):
# "javascript:alert(1)" is one target, not "javascript:alert(1" and a stray ")".
_TARGET = r"\(\s*<?((?:[^()\s>]|\([^()\s]*\))*)>?(?:\s+(?:\"[^\"\n]*\"|'[^'\n]*'))?\s*\)"
_IMAGE = re.compile(r"!\[([^\]\n]*)\]" + _TARGET)
_LINK = re.compile(r"(?<!!)\[([^\]\n]*)\]" + _TARGET)
_REMOTE = re.compile(r"(?:[A-Za-z][A-Za-z0-9+.-]*:|//|\\\\|/|[A-Za-z]:[\\/])")
_UNSAFE_LINK = re.compile(r"\s*(?:file|javascript|vbscript|data):|\\\\", re.IGNORECASE)
_ACTIVE_HTML = re.compile(
    r"<(?=/?(?:img|script|iframe|frame|object|embed|svg|math|style|link|meta|base|form|input"
    r"|button|video|audio|source|track|picture|image)\b|[A-Za-z][^>\n]*\son[a-z]+\s*="
    r"|a\b[^>\n]*\shref\s*=\s*[\"']?\s*(?:javascript|vbscript|file|data):)",
    re.IGNORECASE,
)
_CODE_SPAN = re.compile(r"(`+)(?:.*?[^`])?\1(?!`)", re.DOTALL)


def _image(found: re.Match[str]) -> str:
    alt, address = found.group(1).strip(), found.group(2)
    if address.lower().startswith("data:image/") or not _REMOTE.match(address):
        return found.group(0)
    return f"[image: {alt}]" if alt else "[image]"


def _link(found: re.Match[str]) -> str:
    text, address = found.group(1), found.group(2)
    return text if _UNSAFE_LINK.match(address) else found.group(0)


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
    text, images = _IMAGE.subn(_image, text)
    kept_images = len(_IMAGE.findall(text))
    text, links = _LINK.subn(_link, text)
    kept_links = len(_LINK.findall(text))
    text, tags = _ACTIVE_HTML.subn("&lt;", text)
    return text, (images - kept_images) + (links - kept_links) + tags


def safe_output(markdown: str) -> tuple[str, int]:
    """``markdown`` with nothing that fetches or runs when opened, and how many things changed."""
    changed = 0

    def fix(text: str) -> str:
        nonlocal changed
        fixed, count = _outside_spans(text)
        changed += count
        return fixed

    return outside_code(markdown, fix), changed
