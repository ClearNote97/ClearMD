"""Builders shared by the ODT verification regressions (feature 003, N1-N21)."""

import io
import time
import zipfile
from pathlib import Path

from builders.odt_package import _odt_xml, odt_package
from builders.odt_styles import ODT_AUTOMATIC_STYLES
from markdown_it import MarkdownIt

from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.odt import OdtConverter

MATH = 'xmlns="http://www.w3.org/1998/Math/MathML"'


PARSER = MarkdownIt("commonmark")


NOTE = "<text:note><text:note-body><text:p>n</text:p></text:note-body></text:note>"


MONO_HTML = '<text:span text:style-name="T7">&lt;img src=x onerror=alert(1)&gt;</text:span>'


MIB = 1024**2


def content(body: str) -> bytes:
    return _odt_xml("document-content", body, automatic=ODT_AUTOMATIC_STYLES)


def convert_bytes(tmp_path: Path, data: bytes) -> tuple[str, set[NoteKind]]:
    path = tmp_path / "v.odt"
    path.write_bytes(data)
    result = OdtConverter().convert(path, None, path.with_suffix(".md"))  # type: ignore[arg-type]
    return result.markdown, {note.kind for note in result.notes}


def convert(
    tmp_path: Path, body: str, extra: dict[str, bytes] | None = None
) -> tuple[str, set[NoteKind]]:
    return convert_bytes(tmp_path, odt_package(content(body), extra=extra))


def md(tmp_path: Path, body: str, extra: dict[str, bytes] | None = None) -> str:
    return convert(tmp_path, body, extra)[0]


def timed(seconds: float, tmp_path: Path, body: str, extra: dict[str, bytes] | None = None) -> str:
    started = time.monotonic()
    markdown = md(tmp_path, body, extra)
    assert time.monotonic() - started < seconds
    return markdown


def manual_zip(entries: list[tuple[str, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in entries:
            method = zipfile.ZIP_STORED if name == "mimetype" else zipfile.ZIP_DEFLATED
            archive.writestr(zipfile.ZipInfo(name), data, compress_type=method)
    return buffer.getvalue()


def manifest(entries: str) -> bytes:
    return (
        '<?xml version="1.0" encoding="UTF-8"?><manifest:manifest '
        'xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">'
        '<manifest:file-entry manifest:full-path="/" '
        'manifest:media-type="application/vnd.oasis.opendocument.text"/>'
        f"{entries}</manifest:manifest>"
    ).encode()


MIME = ("mimetype", b"application/vnd.oasis.opendocument.text")
