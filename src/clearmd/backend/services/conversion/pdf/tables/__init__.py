"""Tables in a PDF page, found from where its words stand (feature 013, ADR-0034).

After Camelot's "stream" method (Vinayak Mehta and contributors, MIT; https://camelot-py.readthedocs.io):
a table is a run of rows whose words leave the same wide gaps, its columns are where those gaps
fall. Camelot reads pdfminer's text; ClearMD reads PDFium's own character boxes, and needs neither
OpenCV nor Ghostscript.

Pure: words in, tables out. Every cell is document text, escaped by the writer (ADR-0023). Every
step sorts first and looks up by bisection, within caps: a hostile page costs about what an
ordinary one does (review of 013).
"""

from clearmd.backend.services.conversion.pdf.tables.find import find_tables
from clearmd.backend.services.conversion.pdf.tables.rows import Table, Word

__all__ = ["Table", "Word", "find_tables"]
