"""Which converter handles each format, and content detection. Built inside the worker."""

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId, Strategy
from clearmd.backend.schemas.models import ConversionResult, Detection


class DocumentConverter(Protocol):
    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        """The Markdown of ``source`` and its notes; raises ``ConversionError`` on failure.

        ``target`` is where the Markdown will be written (links to other files start there).
        """
        ...


class ContentDetector(Protocol):
    def detect(self, path: Path) -> Detection | None: ...


class ConverterRegistry:
    """What the worker can do: convert each format, and detect a format by content."""

    def __init__(
        self,
        converters: Mapping[FormatId, DocumentConverter],
        content_detector: ContentDetector | None = None,
        strategies: Mapping[tuple[FormatId, Strategy], DocumentConverter] | None = None,
    ) -> None:
        self._converters = dict(converters)
        self._content_detector = content_detector
        self._strategies = dict(strategies or {})  # the converters of a non-default strategy

    def detect_content(self, path: Path) -> Detection | None:
        return self._content_detector.detect(path) if self._content_detector else None

    def for_format(
        self, format_id: FormatId, strategy: Strategy = Strategy.FULL
    ) -> DocumentConverter:
        found = (
            self._converters.get(format_id)
            if strategy is Strategy.FULL
            else self._strategies.get((format_id, strategy))
        )
        if found is None:
            raise ConversionError(
                ErrorCode.UNSUPPORTED_FORMAT, f"no converter for {format_id} ({strategy})"
            )
        return found


def build_registry() -> ConverterRegistry:
    """The real registry: markitdown, ClearMD's own converters and content signatures."""
    from clearmd.backend.services.conversion.eml import EmlConverter
    from clearmd.backend.services.conversion.html import ArticleConverter
    from clearmd.backend.services.conversion.markitdown_adapter import MarkItDownConverter
    from clearmd.backend.services.conversion.odt import OdtConverter
    from clearmd.backend.services.conversion.pdf import PdfConverter
    from clearmd.backend.services.conversion.rtf import RtfConverter
    from clearmd.backend.services.conversion.subtitles import SubtitlesConverter
    from clearmd.backend.services.conversion.tex import TexConverter
    from clearmd.backend.services.conversion.xlsx import XlsxConverter
    from clearmd.backend.services.detection.content import SignatureDetector

    markitdown = MarkItDownConverter()
    converters: dict[FormatId, DocumentConverter] = dict.fromkeys(markitdown.converters, markitdown)
    converters[FormatId.TEX] = TexConverter()
    converters[FormatId.ODT] = OdtConverter()
    converters[FormatId.PDF] = PdfConverter()  # PDFium + ClearMD's cleaning (ADR-0030)
    converters[FormatId.XLSX] = XlsxConverter()  # openpyxl, no pandas (ADR-0032)
    converters[FormatId.EML] = EmlConverter()  # its HTML body: ClearMD's page writer (039)
    converters[FormatId.RTF] = RtfConverter()
    converters[FormatId.SRT] = converters[FormatId.VTT] = SubtitlesConverter()
    article = ArticleConverter()  # no article: the whole page, written by ClearMD too
    return ConverterRegistry(
        converters,
        content_detector=SignatureDetector(),
        strategies={(FormatId.HTML, Strategy.ARTICLE): article},
    )
