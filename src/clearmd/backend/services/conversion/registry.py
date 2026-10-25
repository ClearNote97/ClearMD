"""Which converter handles each format, and content detection. Built inside the worker."""

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import ConversionResult, Detection


class DocumentConverter(Protocol):
    def convert(self, source: Path, detection: Detection) -> ConversionResult:
        """The Markdown of ``source`` and its notes; raises ``ConversionError`` on failure."""
        ...


class ContentDetector(Protocol):
    def detect(self, path: Path) -> Detection | None: ...


class ConverterRegistry:
    """What the worker can do: convert each format, and detect a format by content."""

    def __init__(
        self,
        converters: Mapping[FormatId, DocumentConverter],
        content_detector: ContentDetector | None = None,
    ) -> None:
        self._converters = dict(converters)
        self._content_detector = content_detector

    def detect_content(self, path: Path) -> Detection | None:
        return self._content_detector.detect(path) if self._content_detector else None

    def for_format(self, format_id: FormatId) -> DocumentConverter:
        try:
            return self._converters[format_id]
        except KeyError:
            raise ConversionError(
                ErrorCode.UNSUPPORTED_FORMAT, f"no converter for {format_id}"
            ) from None


def build_registry() -> ConverterRegistry:
    """The real registry: markitdown for every format of feature 001, magika for content."""
    from clearmd.backend.services.conversion.markitdown_adapter import MarkItDownConverter
    from clearmd.backend.services.detection.content import MagikaDetector

    markitdown = MarkItDownConverter()
    return ConverterRegistry(dict.fromkeys(FormatId, markitdown), content_detector=MagikaDetector())
