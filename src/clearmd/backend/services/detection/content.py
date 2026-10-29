"""Detection by content, by ClearMD's own signatures (feature 010, ADR-0032). Worker process only.

It runs only for files without an extension (``content_policy``): a document saved without one
(``escaneado``, ``README``). It reads the first 64 KiB, and for a ZIP the names of its entries (no
entry is decompressed but the few bytes of an ODF or EPUB ``mimetype``). magika did this with a
63 MB model; these are the formats ClearMD converts, and their signatures are fixed.

Anything else (a binary, a script, a ZIP of something else) is "unsupported": what is not
contemplated is not accepted.
"""

import csv
import io
import json
import re
import zipfile
from pathlib import Path

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.services.conversion.safe_files import open_regular_file

SAMPLE = 64 * 1024
MIMETYPE_BYTES = 128
MAX_ENTRIES = 50_000  # as many as a ZIP may hold to be converted (ADR-0015)

_ZIP_PARTS = (
    ("word/document.xml", FormatId.DOCX),
    ("ppt/presentation.xml", FormatId.PPTX),
    ("xl/workbook.xml", FormatId.XLSX),
)
_MIMETYPES = {
    b"application/vnd.oasis.opendocument.text": FormatId.ODT,
    b"application/epub+zip": FormatId.EPUB,
}
_HTML = re.compile(
    r"^\s*(?:<!--.*?-->\s*)*<(?:!doctype\s+html|html[\s>])", re.IGNORECASE | re.DOTALL
)
_TEX = re.compile(r"\\(?:documentclass|begin\{document\}|section\*?\{|chapter\*?\{)")
# A program, not a document: a shebang, or the lines a script starts with.
_CODE = re.compile(
    r"\A#!|^(?:import \w|from [\w.]+ import |def \w+\(|class \w+[(:]|#include\s*<|"
    r"package \w|public (?:static )?(?:class|void)|function \w+\()",
    re.MULTILINE,
)
_CSV_DELIMITERS = ",;\t|"
_BOMS = ((b"\xef\xbb\xbf", "utf-8"), (b"\xff\xfe", "utf-16-le"), (b"\xfe\xff", "utf-16-be"))


def _text(sample: bytes) -> str | None:
    """The sample as text, or None for binary data (a NUL, or bytes no text encoding makes)."""
    for bom, encoding in _BOMS:
        if sample.startswith(bom):
            return sample[len(bom) :].decode(encoding, errors="ignore")
    if b"\x00" in sample:
        return None
    try:
        return sample.decode("utf-8")
    except UnicodeDecodeError as error:
        if error.start >= len(sample) - 3:  # the sample cut a character in two
            return sample[: error.start].decode("utf-8")
    text = sample.decode("latin-1")
    controls = sum(1 for char in text if ord(char) < 0x20 and char not in "\t\n\r\f")
    return text if controls <= len(text) // 100 else None


def _is_csv(text: str) -> bool:
    """Several lines with the same number of one delimiter in each (at least one)."""
    lines = [line for line in text.splitlines()[:20] if line.strip()]
    if len(lines) < 2:
        return False
    for delimiter in _CSV_DELIMITERS:
        try:
            rows = list(csv.reader(io.StringIO("\n".join(lines)), delimiter=delimiter))
        except csv.Error:
            continue
        widths = {len(row) for row in rows[:-1]}  # the last line may be cut
        if len(widths) == 1 and widths.pop() >= 2:
            return True
    return False


def _is_notebook(text: str) -> bool:
    stripped = text.lstrip()
    if not stripped.startswith("{") or '"cells"' not in text or '"nbformat"' not in text:
        return False
    try:
        return isinstance(json.loads(text).get("cells"), list)
    except ValueError:  # cut by the sample: its keys are enough
        return True


def _zip_format(path: Path) -> FormatId | None:
    try:
        with open_regular_file(path) as stream, zipfile.ZipFile(stream) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ENTRIES:
                return None
            names = {entry.filename for entry in entries}
            for part, format_id in _ZIP_PARTS:
                if part in names and "[Content_Types].xml" in names:
                    return format_id
            if "mimetype" in names:
                with archive.open("mimetype") as entry:
                    mimetype = entry.read(MIMETYPE_BYTES).strip()
                return _MIMETYPES.get(mimetype)
    except (OSError, zipfile.BadZipFile, ValueError, KeyError, EOFError):
        return None
    return None


def detect_format(path: Path) -> FormatId | None:
    with open_regular_file(path) as stream:
        sample = stream.read(SAMPLE)
    if sample.startswith(b"%PDF-"):
        return FormatId.PDF if b"obj" in sample else None  # a header and garbage is no PDF
    if sample.startswith(b"PK\x03\x04"):
        return _zip_format(path)
    text = _text(sample)
    if text is None or not text.strip():
        return None
    if _HTML.match(text):
        return FormatId.HTML
    if _is_notebook(text):
        return FormatId.IPYNB
    if _TEX.search(text):
        return FormatId.TEX
    if _CODE.search(text):
        return None
    if _is_csv(text):
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
