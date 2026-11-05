"""The PDF generator."""

import random
from pathlib import Path

from benchlib.common import _line


def _pdf_page_stream(rng: random.Random) -> bytes:
    lines = " 0 -14 Td ".join(f"({_line(rng)}) Tj" for _ in range(48))
    return f"BT /F1 10 Tf 50 760 Td {lines} ET".encode("latin-1")


def make_pdf(path: Path, size: int, rng: random.Random) -> None:
    """Text-only pages, uncompressed streams, written with a correct xref table."""
    offsets: list[int] = []
    page_ids: list[int] = []
    with path.open("wb") as out:
        out.write(b"%PDF-1.4\n")

        def obj(number: int, body: bytes) -> None:
            while len(offsets) < number:
                offsets.append(0)
            offsets[number - 1] = out.tell()
            out.write(f"{number} 0 obj\n".encode() + body + b"\nendobj\n")

        obj(3, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        number = 4
        while out.tell() < size:
            stream = _pdf_page_stream(rng)
            obj(number, b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
            obj(
                number + 1,
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                b"/Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>" % number,
            )
            page_ids.append(number + 1)
            number += 2
        kids = " ".join(f"{page} 0 R" for page in page_ids)
        obj(2, f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode())
        obj(1, b"<< /Type /Catalog /Pages 2 0 R >>")
        xref_at = out.tell()
        out.write(f"xref\n0 {len(offsets) + 1}\n0000000000 65535 f \n".encode())
        for offset in offsets:
            out.write(f"{offset:010d} 00000 n \n".encode())
        out.write(
            f"trailer\n<< /Size {len(offsets) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_at}\n%%EOF\n".encode()
        )
