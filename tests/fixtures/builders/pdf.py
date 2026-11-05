"""PDF fixtures: a hand-written page and an encrypted copy."""

import io

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, ByteStringObject

from builders.common import PDF_PASSWORD


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
