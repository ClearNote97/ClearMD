"""Detection by content, by ClearMD's own signatures (feature 010, ADR-0032). Worker process only.

It runs only for files without an extension (``content_policy``): a document saved without one
(``escaneado``, ``README``). It reads the first 64 KiB; for a ZIP, the names of its entries, after
the same index checks as planning (``archive``), and the few bytes of an ODF or EPUB ``mimetype``,
stored as their specifications require. magika did this with a 63 MB model; these are the formats
ClearMD converts, and their signatures are fixed.

Anything else (a binary, a program, a ZIP of something else) is "unsupported": what is not
contemplated is not accepted. Every check is linear in the sample (no regular expression that
can backtrack, security audit of 010).
"""

from pathlib import Path

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.services.conversion.safe_files import open_regular_file
from clearmd.backend.services.detection.text_signatures import (
    CODE,
    TEX,
    TEX_COMMANDS,
    as_text,
    is_csv,
    is_html,
    is_notebook,
    without_fences,
)
from clearmd.backend.services.detection.zip_signatures import zip_format

SAMPLE = 64 * 1024


def detect_format(path: Path) -> FormatId | None:
    with open_regular_file(path) as stream:
        sample = stream.read(SAMPLE)
        cut = bool(stream.read(1))
    if sample.startswith(b"%PDF-"):
        return FormatId.PDF if b"obj" in sample else None  # a header and garbage is no PDF
    if sample.startswith(b"PK\x03\x04"):
        return zip_format(path)
    text = as_text(sample)
    if text is None or not text.strip():
        return None
    if is_html(text):
        return FormatId.HTML
    if is_notebook(text, cut):
        return FormatId.IPYNB
    if CODE.search(without_fences(text)):
        return None
    if TEX.search(text) or len(TEX_COMMANDS.findall(text)) >= 2:
        return FormatId.TEX
    if is_csv(text, cut):
        return FormatId.CSV
    return FormatId.TXT


class SignatureDetector:
    """A ``ContentDetector``: the format of a file without an extension, from its content."""

    def detect(self, path: Path) -> Detection | None:
        try:
            format_id = detect_format(path)
        except OSError:
            return None
        return Detection(format_id, DetectionMethod.CONTENT) if format_id is not None else None
