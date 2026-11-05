"""Constants and ZIP helpers shared by every fixture builder."""

import io
import re
import zipfile
from pathlib import Path

DOCUMENTS_DIR = Path(__file__).parent.parent / "documents"

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
