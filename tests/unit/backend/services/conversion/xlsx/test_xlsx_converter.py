"""ClearMD's own Excel converter (feature 010, ADR-0032)."""

import datetime as dt
from pathlib import Path

import openpyxl
import pytest
from markdown_it import MarkdownIt
from support import DOCUMENTS_DIR

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.services.conversion.xlsx import XlsxConverter

DETECTION = Detection(FormatId.XLSX, DetectionMethod.EXTENSION)


def convert(path: Path) -> str:
    return XlsxConverter().convert(path, DETECTION, path.with_suffix(".md")).markdown


def workbook(tmp_path: Path, sheets: dict[str, list[list[object]]]) -> Path:
    book = openpyxl.Workbook()
    book.remove(book.active)
    for title, rows in sheets.items():
        sheet = book.create_sheet(title)
        for row in rows:
            sheet.append(row)
    path = tmp_path / "book.xlsx"
    book.save(path)
    return path


def test_the_fixture_reads_as_markitdown_wrote_it() -> None:
    assert convert(DOCUMENTS_DIR / "sample.xlsx") == (
        "## Data\n\n| Name | Value |\n| --- | --- |\n| fixture-xlsx | 1 |\n| second row | 2 |\n"
    )


def test_every_sheet_numbers_dates_and_empty_rows(tmp_path: Path) -> None:
    path = workbook(
        tmp_path,
        {
            "Ventas": [["Mes", "Total", "Fecha"], ["Enero", 3.0, dt.datetime(2026, 1, 31)],
                       [None, None, None], ["Febrero", 2.5, dt.date(2026, 2, 28)]],
            "Vacía": [],
        },
    )  # fmt: skip
    markdown = convert(path)
    assert "## Ventas" in markdown and "## Vacía" in markdown
    assert "| Enero | 3 | 2026-01-31 |" in markdown and "| Febrero | 2.5 | 2026-02-28 |" in markdown
    assert "|  |  |  |" not in markdown  # the empty row is gone


@pytest.mark.parametrize(
    "hostile", ["a | b", "<script>x</script>", "[x](javascript:1)", "# heading", "line\nbreak"]
)
def test_cells_never_become_markdown_they_did_not_write(tmp_path: Path, hostile: str) -> None:
    markdown = convert(workbook(tmp_path, {"S": [["Header"], [hostile]]}))
    tokens = MarkdownIt("commonmark", {"html": True}).enable("table").parse(markdown)
    kinds = {token.type for token in tokens}
    assert "html_block" not in kinds and "heading_open" in kinds  # only the sheet's own heading
    links = [
        c for t in tokens for c in (t.children or []) if c.type in {"link_open", "html_inline"}
    ]
    assert links == []
    assert sum(1 for t in tokens if t.type == "td_open") == 1  # "a | b" stays one cell


def test_a_sheet_title_is_text(tmp_path: Path) -> None:
    markdown = convert(workbook(tmp_path, {"Q1 #": [["x"]]}))
    assert markdown.startswith("## Q1 \\#\n")


def test_an_encrypted_workbook_is_password_protected(tmp_path: Path) -> None:
    path = tmp_path / "locked.xlsx"
    path.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 600)
    with pytest.raises(ConversionError) as raised:
        convert(path)
    assert raised.value.code is ErrorCode.PASSWORD_PROTECTED


def test_a_broken_workbook_is_corrupt(tmp_path: Path) -> None:
    path = tmp_path / "broken.xlsx"
    path.write_bytes(b"PK\x03\x04 not really a workbook")
    with pytest.raises(ConversionError) as raised:
        convert(path)
    assert raised.value.code is ErrorCode.CORRUPT_FILE
