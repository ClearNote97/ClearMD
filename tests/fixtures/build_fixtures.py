"""Build the sample documents used by the tests, reproducibly.

Run inside the container:  uv run python tests/fixtures/build_fixtures.py

Every document carries a unique marker (``MARKERS``) so a test can check that its text survived the
conversion. ZIP-based documents get fixed timestamps, so rebuilding yields the same bytes.
"""

import io
import json
import re
import zipfile
from collections.abc import Callable
from pathlib import Path

# openpyxl and python-pptx come with markitdown's xlsx/pptx extras; openpyxl ships no type
# information (mypy override in pyproject.toml).
import openpyxl
import pptx
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, ByteStringObject

DOCUMENTS_DIR = Path(__file__).parent / "documents"

FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)
FIXED_ISO_TIME = "2026-01-01T00:00:00Z"
PDF_PASSWORD = "clearmd"
BOMB_UNCOMPRESSED_BYTES = 20 * 1024**2

MARKERS = {
    "sample.pdf": "fixture-pdf",
    "encrypted.pdf": "fixture-pdf",
    "sample.docx": "fixture-docx",
    "docx_without_extension": "fixture-docx",
    "sample.pptx": "fixture-pptx",
    "sample.xlsx": "fixture-xlsx",
    "sample.html": "fixture-html",
    "sample.csv": "fixture-csv",
    "sample.epub": "fixture-epub",
    "sample.ipynb": "fixture-ipynb",
    "sample.txt": "fixture-txt",
}

# Files whose bytes cannot be reproduced exactly (e.g. encryption salts); the tests check their
# properties instead.
NON_DETERMINISTIC: frozenset[str] = frozenset()


# --- ZIP helpers ---------------------------------------------------------------------------------


def _zip_info(name: str, compress_type: int) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIME)
    info.compress_type = compress_type
    info.external_attr = 0o644 << 16
    return info


def _write_zip(entries: list[tuple[str, bytes]], *, stored: frozenset[str] = frozenset()) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in entries:
            compress = zipfile.ZIP_STORED if name in stored else zipfile.ZIP_DEFLATED
            archive.writestr(_zip_info(name, compress), data)
    return buffer.getvalue()


def _normalize_office_zip(data: bytes) -> bytes:
    """Rewrite a library-made Office file with fixed timestamps (entries and core properties)."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = [(info.filename, archive.read(info)) for info in archive.infolist()]
    normalized = []
    for name, content in entries:
        if name == "docProps/core.xml":
            text = content.decode("utf-8")
            text = re.sub(
                r"(<dcterms:(?:created|modified)[^>]*>)[^<]*(</dcterms:)",
                rf"\g<1>{FIXED_ISO_TIME}\g<2>",
                text,
            )
            content = text.encode("utf-8")
        normalized.append((name, content))
    return _write_zip(normalized)


# --- PDF -----------------------------------------------------------------------------------------


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def minimal_pdf(lines: list[str]) -> bytes:
    """A one-page PDF with Helvetica text, written by hand with correct xref offsets."""
    text_ops = " 0 -16 Td ".join(f"({_pdf_escape(line)}) Tj" for line in lines)
    stream = f"BT /F1 12 Tf 72 720 Td {text_ops} ET".encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode()
    out += f"startxref\n{xref_at}\n%%EOF\n".encode()
    return bytes(out)


def encrypted_pdf(source: bytes) -> bytes:
    writer = PdfWriter()
    writer.append(PdfReader(io.BytesIO(source)))
    # A fixed file identifier: with RC4 the encryption keys derive only from it and the passwords.
    file_id = ByteStringObject(b"clearmd-fixture!")
    writer._ID = ArrayObject([file_id, file_id])
    writer.encrypt(user_password=PDF_PASSWORD, algorithm="RC4-128")
    writer.add_metadata({"/Producer": "ClearMD fixtures"})
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


# --- Office and e-book documents ------------------------------------------------------------------

_DOCX_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" '
    'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    "</Types>"
)
_DOCX_ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="word/document.xml"/>'
    "</Relationships>"
)
_DOCX_DOCUMENT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
    'Target="styles.xml"/>'
    "</Relationships>"
)
_DOCX_STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/></w:style>'
    "</w:styles>"
)
_W_NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def _docx_document(body: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f"<w:document {_W_NS}><w:body>{body}</w:body></w:document>"
    )


def minimal_docx() -> bytes:
    body = (
        '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
        "<w:r><w:t>ClearMD fixture</w:t></w:r></w:p>"
        '<w:p><w:r><w:t xml:space="preserve">Text from a DOCX document: </w:t></w:r>'
        f"<w:r><w:rPr><w:b/></w:rPr><w:t>{MARKERS['sample.docx']}</w:t></w:r></w:p>"
    )
    return _write_zip(
        [
            ("[Content_Types].xml", _DOCX_CONTENT_TYPES.encode()),
            ("_rels/.rels", _DOCX_ROOT_RELS.encode()),
            ("word/_rels/document.xml.rels", _DOCX_DOCUMENT_RELS.encode()),
            ("word/styles.xml", _DOCX_STYLES.encode()),
            ("word/document.xml", _docx_document(body).encode()),
        ]
    )


def zip_bomb_docx() -> bytes:
    """A docx whose document.xml expands ~1000:1 — small on disk, large in memory."""
    paragraph = b"<w:p><w:r><w:t>ClearMD zip bomb fixture</w:t></w:r></w:p>"
    head = f'<?xml version="1.0" encoding="UTF-8"?><w:document {_W_NS}><w:body>'.encode()
    tail = b"</w:body></w:document>"
    repeats = (BOMB_UNCOMPRESSED_BYTES - len(head) - len(tail)) // len(paragraph)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compresslevel=9) as archive:
        archive.writestr(
            _zip_info("[Content_Types].xml", zipfile.ZIP_DEFLATED), _DOCX_CONTENT_TYPES
        )
        archive.writestr(_zip_info("_rels/.rels", zipfile.ZIP_DEFLATED), _DOCX_ROOT_RELS)
        with archive.open(_zip_info("word/document.xml", zipfile.ZIP_DEFLATED), "w") as entry:
            entry.write(head)
            chunk = paragraph * 4096
            for _ in range(repeats // 4096):
                entry.write(chunk)
            entry.write(paragraph * (repeats % 4096))
            entry.write(tail)
    return buffer.getvalue()


def minimal_pptx() -> bytes:
    presentation = pptx.Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[1])
    slide.shapes.title.text = "ClearMD fixture"
    slide.placeholders[1].text = f"Text from a PPTX slide: {MARKERS['sample.pptx']}"
    buffer = io.BytesIO()
    presentation.save(buffer)
    return _normalize_office_zip(buffer.getvalue())


def minimal_xlsx() -> bytes:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Data"
    sheet.append(["Name", "Value"])
    sheet.append([MARKERS["sample.xlsx"], 1])
    sheet.append(["second row", 2])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return _normalize_office_zip(buffer.getvalue())


def minimal_epub() -> bytes:
    container = (
        '<?xml version="1.0"?>'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" '
        'media-type="application/oebps-package+xml"/>'
        "</rootfiles></container>"
    )
    opf = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        '<dc:identifier id="id">clearmd-fixture</dc:identifier><dc:title>ClearMD fixture</dc:title>'
        "<dc:creator>ClearMD</dc:creator><dc:language>en</dc:language></metadata>"
        '<manifest><item id="chapter1" href="chapter1.xhtml" '
        'media-type="application/xhtml+xml"/></manifest>'
        '<spine><itemref idref="chapter1"/></spine></package>'
    )
    chapter = (
        '<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml">'
        "<head><title>Chapter 1</title></head><body><h1>Chapter 1</h1>"
        f"<p>Text from an EPUB chapter: {MARKERS['sample.epub']}</p></body></html>"
    )
    return _write_zip(
        [
            ("mimetype", b"application/epub+zip"),
            ("META-INF/container.xml", container.encode()),
            ("OEBPS/content.opf", opf.encode()),
            ("OEBPS/chapter1.xhtml", chapter.encode()),
        ],
        stored=frozenset({"mimetype"}),
    )


# --- Plain-text formats --------------------------------------------------------------------------


def minimal_html() -> bytes:
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8"><title>ClearMD fixture</title></head>'
        "<body><h1>ClearMD fixture</h1>"
        f"<p>Text from an HTML page: {MARKERS['sample.html']}</p></body></html>\n"
    ).encode()


def minimal_csv() -> bytes:
    return f"name,value\n{MARKERS['sample.csv']},1\nsecond row,2\n".encode()


def minimal_txt() -> bytes:
    return f"Text from a plain-text file: {MARKERS['sample.txt']}\n".encode()


def minimal_ipynb() -> bytes:
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# ClearMD fixture\n", MARKERS["sample.ipynb"]],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["1 + 1"],
            },
        ],
        "metadata": {"language_info": {"name": "python"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return (json.dumps(notebook, indent=1) + "\n").encode()


# --- Build ---------------------------------------------------------------------------------------


def build(destination: Path) -> dict[str, Path]:
    """Write every fixture into ``destination`` and return them by name."""
    pdf = minimal_pdf(["ClearMD fixture", f"Text from a PDF document: {MARKERS['sample.pdf']}"])
    docx = minimal_docx()
    builders: dict[str, Callable[[], bytes]] = {
        "sample.pdf": lambda: pdf,
        "encrypted.pdf": lambda: encrypted_pdf(pdf),
        # A PDF header followed by garbage: no objects, no trailer.
        "corrupt.pdf": lambda: b"%PDF-1.4\n" + b"\x00garbage\x00" * 64,
        "sample.docx": lambda: docx,
        "docx_without_extension": lambda: docx,
        # The first half of a valid docx: its ZIP central directory is missing.
        "corrupt.docx": lambda: docx[: len(docx) // 2],
        "zip_bomb.docx": zip_bomb_docx,
        "sample.pptx": minimal_pptx,
        "sample.xlsx": minimal_xlsx,
        "sample.epub": minimal_epub,
        "sample.html": minimal_html,
        "sample.csv": minimal_csv,
        "sample.txt": minimal_txt,
        "sample.ipynb": minimal_ipynb,
    }
    destination.mkdir(parents=True, exist_ok=True)
    written = {}
    for name, make in builders.items():
        path = destination / name
        path.write_bytes(make())
        written[name] = path
    return written


if __name__ == "__main__":
    for path in build(DOCUMENTS_DIR).values():
        shown = path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path
        print(f"{path.stat().st_size:>8}  {shown}")
