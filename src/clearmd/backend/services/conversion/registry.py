"""Which converter handles each format. Built inside the worker process (ADR-0015)."""

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection


class DocumentConverter(Protocol):
    def convert(self, source: Path, detection: Detection) -> str:
        """The Markdown of ``source``; raises ``ConversionError`` on failure."""
        ...


class ConverterRegistry:
    def __init__(self, converters: Mapping[FormatId, DocumentConverter]) -> None:
        self._converters = dict(converters)

    def for_format(self, format_id: FormatId) -> DocumentConverter:
        try:
            return self._converters[format_id]
        except KeyError:
            raise ConversionError(
                ErrorCode.UNSUPPORTED_FORMAT, f"no converter for {format_id}"
            ) from None


def build_registry() -> ConverterRegistry:
    """The real registry: markitdown for every format of feature 001 (one shared instance)."""
    from clearmd.backend.services.conversion.markitdown_adapter import MarkItDownConverter

    markitdown = MarkItDownConverter()
    return ConverterRegistry(dict.fromkeys(FormatId, markitdown))
