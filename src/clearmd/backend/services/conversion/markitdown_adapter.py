"""markitdown's converters behind ClearMD's converter contract (ADR-0004). Worker process only.

Only the converter of the detected format runs, called directly on a stream ClearMD opened itself:
``MarkItDown`` is not used, because when a converter fails it falls back to every built-in one —
a zip renamed ``.pdf`` would reach its ZipConverter (bypassing the zip-bomb check of ADR-0015) and
an image would run exiftool (security review of feature 001).

The exception mapping was confirmed against the fixtures (T04): a truncated docx raises
``BadZipFile``. PDF is ClearMD's own since feature 008 (ADR-0030).
"""

import io
import zipfile
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import BinaryIO
from xml.etree.ElementTree import ParseError
from xml.parsers.expat import ExpatError

from markitdown import DocumentConverter, StreamInfo, UnsupportedFormatException
from markitdown.converters import (
    CsvConverter,
    DocxConverter,
    EpubConverter,
    HtmlConverter,
    IpynbConverter,
    PlainTextConverter,
    PptxConverter,
)

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import ConversionResult, Detection
from clearmd.backend.services.conversion.csv_dialect import with_commas
from clearmd.backend.services.conversion.images import ImageSink, epub_images, take_data_images
from clearmd.backend.services.conversion.safe_files import open_regular_file

_CORRUPT: tuple[type[BaseException], ...] = (
    zipfile.BadZipFile,
    ParseError,
    ExpatError,
)
# lxml (used by python-pptx) is matched by name: it ships no type information.
_CORRUPT_BY_NAME = frozenset({"XMLSyntaxError"})


def _describe(error: BaseException) -> str:
    message = str(error).strip()
    return f"{type(error).__name__}: {message}" if message else type(error).__name__


def _code_for(error: BaseException) -> ErrorCode:
    if isinstance(error, MemoryError):
        return ErrorCode.OUT_OF_MEMORY
    if isinstance(error, _CORRUPT) or type(error).__name__ in _CORRUPT_BY_NAME:
        return ErrorCode.CORRUPT_FILE
    if isinstance(error, PermissionError):
        return ErrorCode.SOURCE_UNREADABLE
    return ErrorCode.CONVERSION_FAILED


def map_exception(error: Exception) -> ConversionError:
    """The ClearMD error for anything a converter (or the file system) raised."""
    if isinstance(error, UnsupportedFormatException):
        return ConversionError(ErrorCode.UNSUPPORTED_FORMAT, _describe(error))
    attempts = getattr(error, "attempts", None)  # markitdown's FileConversionException
    if attempts is not None or type(error).__name__ == "FileConversionException":
        causes = [attempt.exc_info[1] for attempt in attempts or [] if attempt.exc_info]
        for cause in causes:
            code = _code_for(cause)
            if code is not ErrorCode.CONVERSION_FAILED:
                return ConversionError(code, _describe(cause))
        detail = _describe(causes[0]) if causes else _describe(error)
        return ConversionError(ErrorCode.CONVERSION_FAILED, detail)
    return ConversionError(_code_for(error), _describe(error))


def _open_regular_file(source: Path) -> BinaryIO:
    try:
        return open_regular_file(source)
    except OSError as error:
        raise ConversionError(ErrorCode.SOURCE_UNREADABLE, _describe(error)) from error


def _converters() -> Mapping[FormatId, DocumentConverter]:
    # Some of markitdown's converters have untyped constructors.
    return MappingProxyType(
        {
            FormatId.DOCX: DocxConverter(),  # type: ignore[no-untyped-call]
            FormatId.PPTX: PptxConverter(),  # type: ignore[no-untyped-call]
            FormatId.HTML: HtmlConverter(),
            FormatId.CSV: CsvConverter(),  # type: ignore[no-untyped-call]
            FormatId.EPUB: EpubConverter(),  # type: ignore[no-untyped-call]
            FormatId.IPYNB: IpynbConverter(),
            FormatId.TXT: PlainTextConverter(),
        }
    )


class MarkItDownConverter:
    """markitdown's converter for the detected format, and nothing else."""

    def __init__(self) -> None:
        self.converters = _converters()

    def convert(
        self,
        source: Path,
        detection: Detection,
        target: Path,
        *,
        images: ImageSink | None = None,
    ) -> ConversionResult:
        converter = self.converters[detection.format]
        hint = StreamInfo(extension=f".{detection.format.value}", filename=source.name)
        # With an images folder (012): docx and pptx pictures come back as data: URIs, made
        # files by the sink; an EPUB's are read from its package.
        options = {"keep_data_uris": True} if images is not None else {}
        with _open_regular_file(source) as opened:
            stream: BinaryIO = opened
            if detection.format is FormatId.CSV:  # semicolons, tabs: rewritten with commas
                rewritten = with_commas(opened.read())
                opened.seek(0)
                if rewritten is not None:
                    stream = io.BytesIO(rewritten)
                    hint = StreamInfo(extension=".csv", filename=source.name, charset="utf-8")
            try:
                result = converter.convert(stream, hint, **options)
            except Exception as error:
                raise map_exception(error) from error
        markdown = take_data_images(result.markdown, images)
        if images is not None and detection.format is FormatId.EPUB:
            markdown = epub_images(source, markdown, images)
        return ConversionResult(markdown)  # markitdown reports nothing it skipped
