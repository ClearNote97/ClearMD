"""HTML article mode (ADR-0025): trafilatura finds the article, ClearMD writes it.

trafilatura is given the page's bytes only (it never fetches anything: ADR-0005) and returns the
article's tree, read again by ClearMD's limited XML reader and written by ``render``. No article,
or one with less than ``MIN_ARTICLE_CHARACTERS`` of text, converts the whole page (markitdown)
with a note.
Imported only inside the worker.
"""

import re
from pathlib import Path

import trafilatura
from lxml import etree  # type: ignore[import-untyped]  # trafilatura's own parser

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.models import ConversionResult, Detection
from clearmd.backend.schemas.notes import ConversionNote, NoteKind
from clearmd.backend.services.conversion.html.render import ArticleRenderer
from clearmd.backend.services.conversion.registry import DocumentConverter
from clearmd.backend.services.conversion.safe_files import NotARegularFile, read_regular_file
from clearmd.backend.services.conversion.xmltree import Element, XmlRefused, parse_part

MIN_ARTICLE_CHARACTERS = 200  # the fixture's login page has about 50; a short article, 500+
MAX_PAGE_BYTES = 256 * 1024**2
_LANGUAGE = re.compile(rb"<html\b[^>]*?\blang\s*=\s*[\"']?([A-Za-z]{2,3})", re.IGNORECASE)


class ArticleConverter:
    def __init__(self, full_page: DocumentConverter) -> None:
        self._full_page = full_page

    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        try:
            page = read_regular_file(source, MAX_PAGE_BYTES)
        except (OSError, NotARegularFile) as error:
            raise ConversionError(
                ErrorCode.SOURCE_UNREADABLE, f"{type(error).__name__}: {error}"
            ) from error
        main = _article(page)
        if main is None or len(main.text().strip()) < MIN_ARTICLE_CHARACTERS:
            whole = self._full_page.convert(source, detection, target)
            note = ConversionNote(NoteKind.ARTICLE_NOT_FOUND, ())
            return ConversionResult(whole.markdown, (note, *whole.notes))
        language = _LANGUAGE.search(page[:65_536])
        renderer = ArticleRenderer(
            language=language.group(1).decode("ascii") if language else "en",
            source_size=len(main.text()),
        )
        return ConversionResult(renderer.document(main), renderer.notes())


def _article(page: bytes) -> Element | None:
    """The article's tree (trafilatura's ``body``: ``head``, ``p``, ``list``…), read again by
    ClearMD's limited XML reader; ``None`` when there is none or it cannot be read.

    ``bare_extraction`` without metadata and without trafilatura's XML output: both cost more than
    the extraction itself on big pages (benchmark 004: the date search, the duplicate-tag cleanup
    and a fingerprint grew faster than the page) and ClearMD uses neither."""
    found = trafilatura.bare_extraction(
        page,
        include_links=True,
        include_images=True,
        include_tables=True,
        include_formatting=True,
        include_comments=False,
        with_metadata=False,
        deduplicate=False,
    )
    body = getattr(found, "body", None)
    if body is None:
        return None
    try:
        return parse_part(etree.tostring(body, encoding="utf-8"))
    except XmlRefused:
        return None  # nothing ClearMD can read: the whole page instead
