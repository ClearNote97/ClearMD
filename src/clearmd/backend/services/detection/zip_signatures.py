"""A ZIP's format by its parts (DOCX, PPTX, XLSX, ODT, EPUB), after planning's index checks."""

import lzma
import zipfile
import zlib
from pathlib import Path

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.services.conversion.safe_files import open_regular_file
from clearmd.backend.use_cases.archive import MAX_DIRECTORY_BYTES, end_record

MIMETYPE_BYTES = 128
MAX_ENTRIES = 50_000  # as many as a ZIP may hold to be converted (ADR-0015)

ZIP_PARTS = (
    ("word/document.xml", FormatId.DOCX),
    ("ppt/presentation.xml", FormatId.PPTX),
    ("xl/workbook.xml", FormatId.XLSX),
)
MIMETYPES = {
    b"application/vnd.oasis.opendocument.text": FormatId.ODT,
    b"application/epub+zip": FormatId.EPUB,
}
ZIP_ERRORS = (
    OSError, zipfile.BadZipFile, ValueError, KeyError, EOFError, RuntimeError,
    NotImplementedError, zlib.error, lzma.LZMAError,
)  # fmt: skip


def zip_format(path: Path) -> FormatId | None:
    """A ZIP's format by its parts, after the index checks planning makes (a huge index is never
    loaded); a ``mimetype`` read only when stored and small, as ODF and EPUB require."""
    try:
        end = end_record(path)
        if end is None or end[0] > MAX_ENTRIES or end[1] > MAX_DIRECTORY_BYTES:
            return None
        with open_regular_file(path) as stream, zipfile.ZipFile(stream) as archive:
            names = set(archive.namelist())
            for part, format_id in ZIP_PARTS:
                if part in names and "[Content_Types].xml" in names:
                    return format_id
            if "mimetype" not in names:
                return None
            info = archive.getinfo("mimetype")
            if info.compress_type != zipfile.ZIP_STORED or info.file_size > MIMETYPE_BYTES:
                return None
            with archive.open(info) as entry:
                mimetype = entry.read(MIMETYPE_BYTES).strip()
            return MIMETYPES.get(mimetype)
    except ZIP_ERRORS:
        return None
