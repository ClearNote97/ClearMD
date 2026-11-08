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
    TEX = "tex"  # ClearMD's own converter (feature 002)
    ODT = "odt"  # ClearMD's own converter, standard library only (feature 003)
    EML = "eml"  # e-mail, ClearMD's own converter (feature 029)
    RTF = "rtf"  # Rich Text Format, ClearMD's own converter (feature 029)
    SRT = "srt"  # subtitles (feature 029)
    VTT = "vtt"  # WebVTT subtitles (feature 029)
    MARKDOWN = "md"  # only split, never converted (feature 024)


class Strategy(StrEnum):
    """How a format is converted when there is more than one way (ADR-0006, ADR-0025): HTML only."""

    FULL = "full"  # the whole page (markitdown)
    ARTICLE = "article"  # only the main content: trafilatura finds it, ClearMD writes it


# The formats that have more than one strategy; every other one is always FULL.
WITH_STRATEGIES: frozenset[FormatId] = frozenset({FormatId.HTML})


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
        ".tex": FormatId.TEX,
        ".odt": FormatId.ODT,
        ".eml": FormatId.EML,
        ".rtf": FormatId.RTF,
        ".srt": FormatId.SRT,
        ".vtt": FormatId.VTT,
    }
)

# The formats ClearMD converts; Markdown is only ever split (feature 024).
CONVERTIBLE: frozenset[FormatId] = frozenset(FormatId) - {FormatId.MARKDOWN}

# ZIP containers: checked from their central directory before converting (ADR-0015).
ZIP_BASED: frozenset[FormatId] = frozenset(
    {FormatId.DOCX, FormatId.PPTX, FormatId.XLSX, FormatId.EPUB, FormatId.ODT}
)

# Recognized only to be skipped with a clear reason (AC-08).
MARKDOWN_EXTENSIONS: frozenset[str] = frozenset({".md", ".markdown"})
ZIP_EXTENSIONS: frozenset[str] = frozenset({".zip"})

OUTPUT_DIR_NAME = "ClearMD_Output"
RESULTS_DIR_NAME = "OutputMD"
SPLIT_DIR_NAME = "OutputSep"  # the parts of split files (ADR-0019, feature 023)
MERGE_DIR_NAME = "OutputUnif"  # merged files (ADR-0019, feature 026)
SUMMARY_NAME = "Resumen_ClearMD.md"
PDF_SUMMARY_NAME = "Resumen_ClearMD.pdf"  # with the summary format "Markdown + PDF" (ADR-0031)
TEMP_SUFFIX = ".clearmd-tmp"


def format_for_extension(extension: str) -> FormatId | None:
    """The format of a file extension such as ``".PDF"``, or ``None`` if it is not supported."""
    return EXTENSIONS.get(extension.lower())
