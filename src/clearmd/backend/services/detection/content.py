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

import csv
import io
import json
import lzma
import re
import zipfile
import zlib
from pathlib import Path

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.services.conversion.safe_files import open_regular_file
from clearmd.backend.use_cases.archive import MAX_DIRECTORY_BYTES, end_record

SAMPLE = 64 * 1024
MIMETYPE_BYTES = 128
MAX_ENTRIES = 50_000  # as many as a ZIP may hold to be converted (ADR-0015)
MAX_COMMENTS = 100  # comments before an HTML page's first tag
MIN_CSV_LINES = 3

_ZIP_PARTS = (
    ("word/document.xml", FormatId.DOCX),
    ("ppt/presentation.xml", FormatId.PPTX),
    ("xl/workbook.xml", FormatId.XLSX),
)
_MIMETYPES = {
    b"application/vnd.oasis.opendocument.text": FormatId.ODT,
    b"application/epub+zip": FormatId.EPUB,
}
_HTML_STARTS = ("<!doctype html", "<html", "<head", "<body")
_NOTEBOOK = re.compile(r'\A\s*\{\s*"cells"\s*:\s*\[')  # nbformat writes its keys sorted
_TEX = re.compile(r"\\(?:documentclass|begin\{document\})")
_TEX_COMMANDS = re.compile(r"\\(?:section|subsection|chapter|begin|usepackage)\*?\{")
# A program, not a document: lines a script or a source file starts with (a fenced block of a
# README is left out first).
_CODE = re.compile(
    r"\A#!|^(?:import \w|from [\w.]+ import |def \w+\(|class \w+[(:]|#include\s*[<\"]|<\?php|"
    r"package [\w.]+;?$|public (?:static )?(?:class|void)|function \w+\(|"
    r"(?:const|let|var) \w+ = require\(|module\.exports|if __name__ == )",
    re.MULTILINE,
)
_BOMS = ((b"\xef\xbb\xbf", "utf-8"), (b"\xff\xfe", "utf-16-le"), (b"\xfe\xff", "utf-16-be"))
_ZIP_ERRORS = (
    OSError, zipfile.BadZipFile, ValueError, KeyError, EOFError, RuntimeError,
    NotImplementedError, zlib.error, lzma.LZMAError,
)  # fmt: skip


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


def _without_fences(text: str) -> str:
    """The text without its fenced blocks (a README's code examples), line by line."""
    kept: list[str] = []
    fence = ""
    for line in text.split("\n"):
        marker = line.lstrip()[:3]
        if marker in ("```", "~~~") and (not fence or marker == fence):
            fence = "" if fence else marker
        elif not fence:
            kept.append(line)
    return "\n".join(kept)


def _is_html(text: str) -> bool:
    """A page: past an XML declaration and its comments, a doctype or an html, head or body."""
    rest = text.lstrip()
    if rest.startswith("<?xml"):
        rest = rest[rest.find("?>") + 2 :].lstrip() if "?>" in rest else ""
    for _ in range(MAX_COMMENTS):
        if not rest.startswith("<!--"):
            break
        end = rest.find("-->")
        if end < 0:
            return False
        rest = rest[end + 3 :].lstrip()
    lowered = rest[:16].lower()
    return any(lowered.startswith(start) for start in _HTML_STARTS)


def _is_notebook(text: str, cut: bool) -> bool:
    if not _NOTEBOOK.match(text) or '"cell_type"' not in text:
        return False
    if cut:  # a notebook with images is far larger than the sample: its start is enough
        return True
    try:
        notebook = json.loads(text)
    except (ValueError, RecursionError):
        return False
    return isinstance(notebook, dict) and "nbformat" in notebook


def _is_csv(text: str, cut: bool) -> bool:
    """Comma-separated rows (the only separator the converter reads), at least three, each with
    the same number of fields; not a Markdown table, not code."""
    lines = [line for line in text.splitlines() if line.strip()]
    if cut:
        lines = lines[:-1]  # the last line may be cut in two
    lines = lines[:50]
    if len(lines) < MIN_CSV_LINES:
        return False
    if any(
        line.lstrip().startswith("|") or line.rstrip().endswith((";", "{", "}")) for line in lines
    ):
        return False
    try:
        rows = list(csv.reader(io.StringIO("\n".join(lines))))
    except csv.Error:
        return False
    widths = {len(row) for row in rows}
    return len(widths) == 1 and widths.pop() >= 2


def _zip_format(path: Path) -> FormatId | None:
    """A ZIP's format by its parts, after the index checks planning makes (a huge index is never
    loaded); a ``mimetype`` read only when stored and small, as ODF and EPUB require."""
    try:
        end = end_record(path)
        if end is None or end[0] > MAX_ENTRIES or end[1] > MAX_DIRECTORY_BYTES:
            return None
        with open_regular_file(path) as stream, zipfile.ZipFile(stream) as archive:
            names = set(archive.namelist())
            for part, format_id in _ZIP_PARTS:
                if part in names and "[Content_Types].xml" in names:
                    return format_id
            if "mimetype" not in names:
                return None
            info = archive.getinfo("mimetype")
            if info.compress_type != zipfile.ZIP_STORED or info.file_size > MIMETYPE_BYTES:
                return None
            with archive.open(info) as entry:
                mimetype = entry.read(MIMETYPE_BYTES).strip()
            return _MIMETYPES.get(mimetype)
    except _ZIP_ERRORS:
        return None


def detect_format(path: Path) -> FormatId | None:
    with open_regular_file(path) as stream:
        sample = stream.read(SAMPLE)
        cut = bool(stream.read(1))
    if sample.startswith(b"%PDF-"):
        return FormatId.PDF if b"obj" in sample else None  # a header and garbage is no PDF
    if sample.startswith(b"PK\x03\x04"):
        return _zip_format(path)
    text = _text(sample)
    if text is None or not text.strip():
        return None
    if _is_html(text):
        return FormatId.HTML
    if _is_notebook(text, cut):
        return FormatId.IPYNB
    if _CODE.search(_without_fences(text)):
        return None
    if _TEX.search(text) or len(_TEX_COMMANDS.findall(text)) >= 2:
        return FormatId.TEX
    if _is_csv(text, cut):
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
