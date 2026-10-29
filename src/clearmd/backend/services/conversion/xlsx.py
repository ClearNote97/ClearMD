"""ClearMD's own Excel converter (feature 010, ADR-0032): each sheet a heading and a table.

openpyxl reads the workbook, read-only and with each formula's last computed value; markitdown
did the same through pandas, which brought numpy and about 100 MB to the executable. The first row
of a sheet is its header, as markitdown wrote it. Every cell is document text, escaped (ADR-0023).
"""

import datetime as dt
import zipfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.utils.exceptions import InvalidFileException

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.models import ConversionResult, Detection
from clearmd.backend.services.conversion.markdown_out import (
    MARK,
    escape_text,
    heading_text,
    neutralize,
    tidy,
)
from clearmd.backend.services.conversion.safe_files import open_regular_file

_OLE = b"\xd0\xcf\x11\xe0"  # an encrypted workbook is an OLE file, not a ZIP


def _shown(value: Any) -> str:
    """A cell as a person reads it: 3 not 3.0, a date without a midnight, text on one line."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, dt.datetime) and value.time() == dt.time():
        return value.date().isoformat()
    if isinstance(value, (dt.date, dt.time)):
        return value.isoformat()
    return " ".join(str(value).split())


def _cell(value: Any) -> str:
    return escape_text(_shown(value)).replace("|", "\\|")


def _rows(sheet: Any) -> list[list[Any]]:
    """The sheet's rows without its empty ones, and as wide as its widest used column."""
    rows = [list(row) for row in sheet.iter_rows(values_only=True)]
    rows = [row for row in rows if any(value not in (None, "") for value in row)]
    width = max(
        (max((i + 1 for i, value in enumerate(row) if value not in (None, "")), default=0)
         for row in rows),
        default=0,
    )  # fmt: skip
    return [row[:width] + [None] * (width - len(row)) for row in rows]


def _table(rows: list[list[Any]]) -> Iterable[str]:
    header, *body = rows
    yield MARK + "| " + " | ".join(_cell(value) for value in header) + " |"
    yield MARK + "| " + " | ".join("---" for _ in header) + " |"
    for row in body:
        yield MARK + "| " + " | ".join(_cell(value) for value in row) + " |"


class XlsxConverter:
    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        try:
            stream = open_regular_file(source)
        except OSError as error:
            raise ConversionError(ErrorCode.SOURCE_UNREADABLE, str(error)) from error
        with stream:
            if stream.read(4) == _OLE:
                raise ConversionError(ErrorCode.PASSWORD_PROTECTED, "an encrypted workbook")
            stream.seek(0)
            try:
                book = openpyxl.load_workbook(stream, read_only=True, data_only=True)
            except (InvalidFileException, zipfile.BadZipFile, KeyError, OSError) as error:
                raise ConversionError(ErrorCode.CORRUPT_FILE, f"{type(error).__name__}") from error
            try:
                blocks = []
                for sheet in book.worksheets:
                    rows = _rows(sheet)
                    name = heading_text(escape_text(" ".join(str(sheet.title).split())))
                    blocks.append(f"{MARK}## {name}")
                    if rows:
                        blocks.append("\n".join(_table(rows)))
            finally:
                book.close()
        return ConversionResult(tidy(neutralize("\n\n".join(blocks))))
