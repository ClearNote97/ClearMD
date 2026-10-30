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

_OLE = b"\xd0\xcf\x11\xe0"  # an encrypted workbook (and an old .xls) is an OLE file, not a ZIP
_ENCRYPTED = "EncryptedPackage".encode("utf-16-le")  # the stream an encrypted workbook holds
SCAN_CHUNK = 1024**2
MAX_ROWS = 1_048_576  # Excel's own limits: a sheet declaring more is not believed
MAX_COLUMNS = 16_384
MAX_CELLS = 20_000_000  # about what fits in a worker's memory as text (code review of 010)


def _shown(value: Any) -> str:
    """A cell as a person reads it: 3 not 3.0, a date without a midnight, text on one line."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else format(value, ".15g")  # 0.3, not noise
    if isinstance(value, dt.datetime):
        return value.date().isoformat() if value.time() == dt.time() else value.isoformat(sep=" ")
    if isinstance(value, (dt.date, dt.time)):
        return value.isoformat()
    return " ".join(str(value).split())


def _cell(value: Any) -> str:
    return escape_text(_shown(value)).replace("|", "\\|")


def _rows(sheet: Any) -> list[list[Any]]:
    """The sheet's rows, read as they are: the size a sheet declares is not trusted, and no row is
    padded while it is read (a tiny file declaring a million wide rows asked gigabytes; asking
    openpyxl for a width pads every row to it: code review, security audit and adversarial check
    of 010). Empty rows go, trailing empty cells go, and the rest is evened out to the widest row,
    within a budget of cells that counts that evening out."""
    sheet.reset_dimensions()
    rows: list[list[Any]] = []
    for index, row in enumerate(sheet.iter_rows(values_only=True)):
        if index >= MAX_ROWS:
            break
        values = list(row[:MAX_COLUMNS])
        while values and values[-1] in (None, ""):
            values.pop()
        if values:
            rows.append(values)
    width = max((len(row) for row in rows), default=0)
    if width * len(rows) > MAX_CELLS:
        raise ConversionError(ErrorCode.OUT_OF_MEMORY, f"more than {MAX_CELLS} cells")
    return [row + [None] * (width - len(row)) for row in rows]


def _table(rows: list[list[Any]]) -> Iterable[str]:
    header, *body = rows
    yield MARK + "| " + " | ".join(_cell(value) for value in header) + " |"
    yield MARK + "| " + " | ".join("---" for _ in header) + " |"
    for row in body:
        yield MARK + "| " + " | ".join(_cell(value) for value in row) + " |"


def _holds(stream: Any, needle: bytes) -> bool:
    """Whether the file holds ``needle``, read a chunk at a time (the OLE directory may be at its
    end)."""
    tail = b""
    while chunk := stream.read(SCAN_CHUNK):
        if needle in tail + chunk:
            return True
        tail = chunk[-len(needle) :]
    return False


class XlsxConverter:
    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        try:
            stream = open_regular_file(source)
        except OSError as error:
            raise ConversionError(ErrorCode.SOURCE_UNREADABLE, str(error)) from error
        with stream:
            if stream.read(4) == _OLE:
                stream.seek(0)
                if _holds(stream, _ENCRYPTED):
                    raise ConversionError(ErrorCode.PASSWORD_PROTECTED, "an encrypted workbook")
                raise ConversionError(ErrorCode.UNSUPPORTED_FORMAT, "an old Excel file (.xls)")
            stream.seek(0)
            try:
                book = openpyxl.load_workbook(stream, read_only=True, data_only=True)
            except (InvalidFileException, zipfile.BadZipFile, KeyError, OSError) as error:
                raise ConversionError(ErrorCode.CORRUPT_FILE, f"{type(error).__name__}") from error
            try:
                blocks = []
                for sheet in book.worksheets:
                    try:
                        rows = _rows(sheet)
                    except ValueError as error:  # a cell reference past Excel's columns
                        raise ConversionError(ErrorCode.CORRUPT_FILE, str(error)[:200]) from error
                    name = heading_text(escape_text(" ".join(str(sheet.title).split())))
                    blocks.append(f"{MARK}## {name}")
                    if rows:
                        blocks.append("\n".join(_table(rows)))
            finally:
                book.close()
        return ConversionResult(tidy(neutralize("\n\n".join(blocks))))
