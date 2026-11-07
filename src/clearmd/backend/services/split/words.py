"""Words, as Split counts them to fit an AI (feature 024, ADR-0045): runs of letters and digits,
and each CJK character on its own (those scripts write no spaces between words)."""

import re
from pathlib import Path

from clearmd.backend.services.split.pdf_pages import open_pdf

# CJK ideographs, kana and hangul: one "word" each.
_CJK = "぀-ヿ㐀-䶿一-鿿가-힯豈-﫿"
_WORD = re.compile(rf"[{_CJK}]|[^\W{_CJK}]+")


def count_words(text: str) -> int:
    return len(_WORD.findall(text))


def page_words(path: Path) -> tuple[int, ...]:
    """The words on each page of a PDF; a page PDFium cannot read counts none."""
    document = open_pdf(path)
    try:
        counts = []
        for page in document:
            try:
                textpage = page.get_textpage()
                try:
                    counts.append(count_words(textpage.get_text_range()))
                finally:
                    textpage.close()
            except Exception:  # noqa: BLE001 -- an unreadable page has no words to count
                counts.append(0)
            finally:
                page.close()
        return tuple(counts)
    finally:
        document.close()
