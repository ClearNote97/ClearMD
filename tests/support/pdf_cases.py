"""Constants and helpers shared by the PDF converter's tests (feature 008)."""

from pathlib import Path

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import ConversionResult, Detection, DetectionMethod
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.pdf import PdfConverter
from support.pdf_builder import Text, build_pdf

DETECTION = Detection(FormatId.PDF, DetectionMethod.EXTENSION)
BODY = [
    "The judicial system facilitates the development of economic, social and",
    "political systems, by regulating interactions based on values such as",
    "impartiality, effectiveness and timeliness in the resolution of conflicts.",
]


def convert(tmp_path: Path, pages: list[list[Text]]) -> ConversionResult:
    source = tmp_path / "doc.pdf"
    source.write_bytes(build_pdf(pages))
    return PdfConverter().convert(source, DETECTION, tmp_path / "doc.md")


def kinds(result: ConversionResult) -> list[NoteKind]:
    return [note.kind for note in result.notes]


def lines_of(markdown: str) -> list[str]:
    return [line for line in markdown.splitlines() if line.strip()]
