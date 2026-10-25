import pytest

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.services.conversion.markitdown_adapter import MarkItDownConverter
from clearmd.backend.services.conversion.registry import ConverterRegistry, build_registry


def test_every_supported_format_has_a_converter() -> None:
    registry = build_registry()
    assert all(isinstance(registry.for_format(fmt), MarkItDownConverter) for fmt in FormatId)


def test_all_formats_share_one_markitdown_instance() -> None:
    registry = build_registry()
    assert registry.for_format(FormatId.PDF) is registry.for_format(FormatId.DOCX)


def test_a_format_without_converter_is_unsupported() -> None:
    with pytest.raises(ConversionError) as raised:
        ConverterRegistry({}).for_format(FormatId.PDF)
    assert raised.value.code is ErrorCode.UNSUPPORTED_FORMAT
