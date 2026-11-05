"""Images in a folder next to the Markdown (feature 012, ADR-0033): pictures drawn in PDFs."""

import io
from pathlib import Path

import pytest
from PIL import Image
from support.images_cases import detection

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.services.conversion.images import ImageSink


def pdf_drawing(draws: str, *, side: int = 2) -> bytes:
    """A PDF page drawing one small RGB image with ``draws`` (its "cm" and "Do" operators)."""
    pixels = bytes([255, 0, 0]) * side * side
    page = f"BT /F1 12 Tf 72 700 Td (Hello) Tj ET {draws}".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R"
        b" >> /XObject << /Im0 5 0 R >> >> /Contents 6 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceRGB"
        b" /BitsPerComponent 8 /Length %d >>\nstream\n"
        % (side, side, len(pixels))
        + pixels
        + b"\nendstream",
        b"<< /Length %d >>\nstream\n" % len(page) + page + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        xref,
    )
    return bytes(out)


def pdf_pictures(tmp_path: Path, data: bytes) -> ImageSink:
    from clearmd.backend.services.conversion.pdf import PdfConverter

    source = tmp_path / "p.pdf"
    source.write_bytes(data)
    sink = ImageSink.for_folder("p_images")
    PdfConverter().convert(source, detection(FormatId.PDF), tmp_path / "p.md", images=sink)
    return sink


def test_a_small_picture_drawn_huge_is_kept_at_its_own_size(tmp_path: Path) -> None:
    sink = pdf_pictures(tmp_path, pdf_drawing("q 12000 0 0 12000 0 0 cm /Im0 Do Q"))
    assert Image.open(io.BytesIO(sink.images[0].data)).size == (2, 2)  # not 12000 x 12000


def test_a_large_picture_drawn_small_keeps_its_pixels(tmp_path: Path) -> None:
    sink = pdf_pictures(tmp_path, pdf_drawing("q 60 0 0 40 72 300 cm /Im0 Do Q", side=300))
    assert Image.open(io.BytesIO(sink.images[0].data)).size == (300, 300)


def test_a_document_has_a_budget_of_pixels(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from clearmd.backend.services.conversion.pdf import reader

    monkeypatch.setattr(reader, "MAX_DOCUMENT_PIXELS", 3)
    sink = pdf_pictures(tmp_path, pdf_drawing("q 100 0 0 100 72 300 cm /Im0 Do Q"))
    assert sink.images == [] and sink.left_out == 1


def test_a_picture_inside_a_form_is_found(tmp_path: Path) -> None:
    form = b"q 100 0 0 100 0 0 cm /Im0 Do Q"
    data = pdf_drawing("/Fm0 Do")
    data = data.replace(
        b"/XObject << /Im0 5 0 R >>", b"/XObject << /Im0 5 0 R /Fm0 7 0 R >>"
    ).replace(
        b"xref",
        b"7 0 obj\n<< /Type /XObject /Subtype /Form /BBox [0 0 200 200] /Resources << /XObject <<"
        b" /Im0 5 0 R >> >> /Length %d >>\nstream\n"
        % len(form)
        + form
        + b"\nendstream\nendobj\nxref",
    )
    assert len(pdf_pictures(tmp_path, data).images) == 1
