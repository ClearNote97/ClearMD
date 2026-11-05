"""From PDFium's lines to Markdown: what a PDF repeats on every page goes, paragraphs and words
broken across lines are joined, headings are told by their size (feature 008, ADR-0030).

No OCR; tables found by where their words stand (feature 013, ``tables``); one reading order
(PDFium's: a page in columns may be read across). Every piece of document text is escaped
(ADR-0023); the block lines ClearMD writes itself (headings, list items, table rows) carry
``MARK``, and what follows a list marker is neutralized like any other line.
"""

from clearmd.backend.services.conversion.pdf.cleaner.clean import Cleaned, clean

__all__ = ["Cleaned", "clean"]
