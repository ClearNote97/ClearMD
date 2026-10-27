"""HTML article mode (ADR-0025): trafilatura finds the article, ClearMD writes it.

trafilatura is given the page's bytes only (it never fetches anything: ADR-0005) and returns the
article's tree, converted to ClearMD's own and written by ``render``. No article (or one with
less than ``MIN_ARTICLE_CHARACTERS`` of text, or a page too complex for trafilatura): the whole
page, written by ClearMD too (``page``), with a note.
Imported only inside the worker.
"""

import html
import re
from pathlib import Path
from typing import Any

import trafilatura
from trafilatura.utils import detect_encoding

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.models import ConversionResult, Detection
from clearmd.backend.schemas.notes import ConversionNote, NoteKind
from clearmd.backend.services.conversion.html.page import page_tree
from clearmd.backend.services.conversion.html.render import ArticleRenderer
from clearmd.backend.services.conversion.safe_files import NotARegularFile, read_regular_file
from clearmd.backend.services.conversion.xmltree import Element, XmlLimits

_MARK = "\ue000"  # ClearMD's mark for its own block lines (markdown_out.MARK)
MIN_ARTICLE_CHARACTERS = 200  # the fixture's login page has about 50; a short article, 500+
MAX_PAGE_BYTES = 256 * 1024**2
# trafilatura's extraction grows faster than linear in the number of elements (audit of 004:
# 40,000 spans take 88 s); a page with more is converted in full, with a note.
MAX_ARTICLE_ELEMENTS = 50_000
_TAG = re.compile(r"<[A-Za-z]")
_LANGUAGE = re.compile(r"<html\b[^>]*?\slang\s*=\s*[\"']?([A-Za-z]{2,3})", re.IGNORECASE)
_TITLE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_CHARSET = re.compile(rb"<meta\b[^>]*?charset\s*=\s*[\"']?\s*([A-Za-z0-9_.:-]+)", re.IGNORECASE)
_BOMS = ((b"\xef\xbb\xbf", "utf-8"), (b"\xff\xfe", "utf-16"), (b"\xfe\xff", "utf-16"))


class ArticleConverter:
    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        try:
            page = read_regular_file(source, MAX_PAGE_BYTES)
        except (OSError, NotARegularFile) as error:
            raise ConversionError(
                ErrorCode.SOURCE_UNREADABLE, f"{type(error).__name__}: {error}"
            ) from error
        # trafilatura is given text (it never decompresses anything), with no character its XML
        # tree refuses: one would lose the whole article (audit of 004).
        text = _xml_safe(_decode(page))
        head = text[:65_536]
        found = _TITLE.search(head)
        title = html.unescape(found.group(1)) if found else ""
        language = _LANGUAGE.search(head)
        renderer = ArticleRenderer(
            language=language.group(1) if language else "en", source_size=len(text)
        )
        reason = None
        main = None
        if len(_TAG.findall(text)) > MAX_ARTICLE_ELEMENTS:
            reason = NoteKind.ARTICLE_TOO_COMPLEX
        else:
            main = _article(text)
            if main is None or len(main.text().strip()) < MIN_ARTICLE_CHARACTERS:
                reason, main = NoteKind.ARTICLE_NOT_FOUND, None
        if main is None:
            # The whole page, written by ClearMD with the same guarantee (the author's choice):
            # article mode never hands a page's own markup or remote images to the Markdown.
            main = page_tree(text) or Element("body")
        markdown = renderer.document(main, title=title)
        notes = renderer.notes()
        if reason is not None:
            notes = (ConversionNote(reason, ()), *notes)
        return ConversionResult(markdown, notes)


_FORBIDDEN = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff\ud800-\udfff]")
_REFERENCE = re.compile(r"&#(?:[xX]([0-9A-Fa-f]{1,8})|([0-9]{1,10}));?")


def _xml_safe(text: str) -> str:
    """Characters XML 1.0 forbids, written or as references, become U+FFFD (shown, harmless)."""

    def reference(found: re.Match[str]) -> str:
        code = int(found.group(1), 16) if found.group(1) else int(found.group(2))
        allowed = (
            code in (0x9, 0xA, 0xD)
            or 0x20 <= code <= 0xD7FF
            or 0xE000 <= code <= 0xFFFD
            or 0x10000 <= code <= 0x10FFFF
        )
        return found.group(0) if allowed else "\ufffd"

    return _REFERENCE.sub(reference, _FORBIDDEN.sub("\ufffd", text))


def _decode(page: bytes) -> str:
    """The page's text: its BOM, then its declared charset, then UTF-8, then a guess."""
    for bom, encoding in _BOMS:
        if page.startswith(bom):
            return page.decode(encoding, errors="replace")
    declared = _CHARSET.search(page[:4096])
    candidates = [declared.group(1).decode("ascii")] if declared else []
    candidates.append("utf-8")
    for candidate in candidates:
        try:
            return page.decode(candidate)
        except (LookupError, UnicodeDecodeError):
            continue
    for guess in detect_encoding(page):
        try:
            return page.decode(guess)
        except (LookupError, UnicodeDecodeError):
            continue
    return page.decode("utf-8", errors="replace")


def _article(page: str) -> Element | None:
    """The article's tree (trafilatura's ``body``: ``head``, ``p``, ``list``…) as ClearMD's own
    element tree; ``None`` when there is none.

    ``bare_extraction`` without metadata: the date search and a fingerprint cost more than the
    extraction itself on big pages (benchmark 004). ``output_format="xml"`` skips the plain-text
    pass, whose memory grows with the square of runs of formatting (audit of 004)."""
    try:
        found = trafilatura.bare_extraction(
            page,
            output_format="xml",
            include_links=True,
            include_images=True,
            include_tables=True,
            include_formatting=True,
            include_comments=False,
            with_metadata=False,
            deduplicate=False,
        )
    except Exception:  # noqa: BLE001 -- anything inside trafilatura: the whole page instead
        return None
    body = getattr(found, "body", None)
    return _from_lxml(body) if body is not None else None


def _from_lxml(root: Any) -> Element | None:
    """lxml's tree → ClearMD's, walked without recursion under the XML reader's limits: no
    serialized round trip, so no character XML forbids can make the article unreadable (audit
    of 004). Comments and processing instructions are dropped; the block mark is stripped and
    line endings become "\n", as ``parse_part`` does."""
    limits = XmlLimits()
    budget = {"elements": 0, "characters": 0}

    def clean(text: str | None) -> str:
        text = (text or "").replace(_MARK, "").replace("\r\n", "\n").replace("\r", "\n")
        budget["characters"] += len(text)
        return text

    def convert(node: Any) -> Element:
        budget["elements"] += 1 + len(node.attrib)
        attributes = {str(k): clean(str(v)) for k, v in node.attrib.items()}
        return Element(str(node.tag), attributes)

    top = convert(root)
    if root.text:
        top.children.append(clean(root.text))
    pending: list[tuple[Any, Element]] = [(child, top) for child in reversed(list(root))]
    while pending:
        node, parent = pending.pop()
        if isinstance(node.tag, str):  # an element (not a comment or an instruction)
            element = convert(node)
            parent.children.append(element)
            if node.text:
                element.children.append(clean(node.text))
            pending.extend((child, element) for child in reversed(list(node)))
        if node.tail:
            parent.children.append(clean(node.tail))
        if budget["elements"] > limits.max_elements or budget["characters"] > limits.max_characters:
            return None
    return top
