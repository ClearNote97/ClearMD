"""Builders shared by the PDF table, equation and script tests (feature 008)."""

from collections.abc import Sequence
from pathlib import Path

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.services.conversion.pdf import PdfConverter
from clearmd.backend.services.conversion.pdf.equations import Placed
from clearmd.backend.services.conversion.pdf.lattice import Rule
from clearmd.backend.services.conversion.pdf.tables import Word
from support.pdf_builder import Box, Text, build_pdf


def grid(
    rows: list[list[str]], *, top: float = 700, columns: tuple[float, ...] = (72, 180, 260, 340)
) -> list[Word]:  # noqa: E501
    words = []
    for index, row in enumerate(rows):
        bottom = top - 14 * index
        for x, text in zip(columns, row, strict=False):
            if text:
                words.append(Word(text, x, x + 5.5 * len(text), bottom, bottom + 10, 10))
    return words


DATA = [
    ["Year", "Median", "CV", "Maximum"],
    ["2012", "0.871", "0.099", "1.0 (3)"],
    ["2013", "0.861", "0.113", "1.0 (3)"],
    ["2014", "0.863", "0.126", "1.0 (4)"],
    ["2015", "0.855", "0.142", "1.0 (4)"],
]


def convert(tmp_path: Path, pages: Sequence[Sequence[Text | Box]]) -> str:
    source = tmp_path / "paper.pdf"
    source.write_bytes(build_pdf(pages))
    detection = Detection(FormatId.PDF, DetectionMethod.EXTENSION)
    return PdfConverter().convert(source, detection, tmp_path / "paper.md").markdown


def upright(rows: list[list[str]], top: float) -> list[Text]:
    return [
        Text(text, top - 16 * index, 10, x=x)
        for index, row in enumerate(rows)
        for x, text in zip((72, 200, 300, 400), row, strict=False)
        if text
    ]


def sideways(rows: list[list[str]], left: float) -> list[Text]:
    """Each row a column of the page, read upwards: the first row at the left."""
    return [
        Text(text, y, 10, x=left + 16 * index, sideways=True)
        for index, row in enumerate(rows)
        for y, text in zip((100, 230, 330, 430), row, strict=False)
        if text
    ]


def header(page: int) -> Text:
    return Text(f"{page} | Journal of Courts", 760, 8)


def downwards(rows: list[list[str]], right: float) -> list[Text]:
    """Each row a column of the page, read downwards: the first row at the right."""
    return [
        Text(text, y, 10, x=right - 16 * index, downwards=True)
        for index, row in enumerate(rows)
        for y, text in zip((700, 570, 470, 370), row, strict=False)
        if text
    ]


def ruled(xs: list[float], ys: list[float]) -> list[Rule]:
    rules = [Rule(True, y, xs[0], xs[-1]) for y in ys]
    return rules + [Rule(False, x, ys[-1], ys[0]) for x in xs]


def placed(text: str, bottom: float, right: float, size: float = 9) -> Placed:
    return Placed(text, bottom + size, bottom, size, right, False)


def label(text: str, left: float, bottom: float) -> Word:
    return Word(text, left, left + 12, bottom, bottom + 9, 9)


def scripted(tmp_path: Path, pieces: list[Text]) -> str:
    return convert(tmp_path, [pieces])
