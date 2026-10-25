"""Supported formats, their extensions and the fixed output names (ADR-0010, ADR-0016)."""

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType


class FormatId(StrEnum):
    """A document format ClearMD can convert. The value is shown upper-cased in the summary."""

    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    HTML = "html"
    CSV = "csv"
    EPUB = "epub"
    IPYNB = "ipynb"
    TXT = "txt"


EXTENSIONS: Mapping[str, FormatId] = MappingProxyType(
    {
        ".pdf": FormatId.PDF,
        ".docx": FormatId.DOCX,
        ".pptx": FormatId.PPTX,
        ".xlsx": FormatId.XLSX,
        ".html": FormatId.HTML,
        ".htm": FormatId.HTML,
        ".csv": FormatId.CSV,
        ".epub": FormatId.EPUB,
        ".ipynb": FormatId.IPYNB,
        ".txt": FormatId.TXT,
    }
)

# ZIP containers: checked from their central directory before converting (ADR-0015).
ZIP_BASED: frozenset[FormatId] = frozenset(
    {FormatId.DOCX, FormatId.PPTX, FormatId.XLSX, FormatId.EPUB}
)

# Recognized only to be skipped with a clear reason (AC-08).
MARKDOWN_EXTENSIONS: frozenset[str] = frozenset({".md", ".markdown"})
ZIP_EXTENSIONS: frozenset[str] = frozenset({".zip"})

OUTPUT_DIR_NAME = "ClearMD_Output"
RESULTS_DIR_NAME = "Output"
SUMMARY_NAME = "Resumen_ClearMD.md"
TEMP_SUFFIX = ".clearmd-tmp"


def format_for_extension(extension: str) -> FormatId | None:
    """The format of a file extension such as ``".PDF"``, or ``None`` if it is not supported."""
    return EXTENSIONS.get(extension.lower())
