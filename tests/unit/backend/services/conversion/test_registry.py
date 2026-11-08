import pytest

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import CONVERTIBLE, FormatId
from clearmd.backend.services.conversion.eml import EmlConverter
from clearmd.backend.services.conversion.markitdown_adapter import MarkItDownConverter
from clearmd.backend.services.conversion.registry import ConverterRegistry, build_registry
from clearmd.backend.services.conversion.rtf import RtfConverter


def test_every_supported_format_has_a_converter() -> None:
    from clearmd.backend.services.conversion.odt import OdtConverter
    from clearmd.backend.services.conversion.pdf import PdfConverter
    from clearmd.backend.services.conversion.tex import TexConverter
    from clearmd.backend.services.conversion.xlsx import XlsxConverter

    registry = build_registry()
    assert isinstance(registry.for_format(FormatId.TEX), TexConverter)
    assert isinstance(registry.for_format(FormatId.ODT), OdtConverter)
    assert isinstance(registry.for_format(FormatId.PDF), PdfConverter)  # ADR-0030
    assert isinstance(registry.for_format(FormatId.XLSX), XlsxConverter)  # ADR-0032
    own = {FormatId.EML, FormatId.RTF, FormatId.SRT, FormatId.VTT}  # feature 029
    assert isinstance(registry.for_format(FormatId.EML), EmlConverter)
    assert isinstance(registry.for_format(FormatId.RTF), RtfConverter)
    assert registry.for_format(FormatId.SRT) is registry.for_format(FormatId.VTT)
    others = CONVERTIBLE - own - {FormatId.TEX, FormatId.ODT, FormatId.PDF, FormatId.XLSX}
    assert all(isinstance(registry.for_format(fmt), MarkItDownConverter) for fmt in others)


def test_all_formats_share_one_markitdown_instance() -> None:
    registry = build_registry()
    assert registry.for_format(FormatId.PPTX) is registry.for_format(FormatId.DOCX)


def test_a_format_without_converter_is_unsupported() -> None:
    with pytest.raises(ConversionError) as raised:
        ConverterRegistry({}).for_format(FormatId.PDF)
    assert raised.value.code is ErrorCode.UNSUPPORTED_FORMAT


def test_the_real_registry_detects_content_by_signature() -> None:
    from support import DOCUMENTS_DIR

    registry = build_registry()
    detection = registry.detect_content(DOCUMENTS_DIR / "docx_without_extension")
    assert detection is not None and detection.format is FormatId.DOCX


def test_a_registry_without_content_detector_detects_nothing() -> None:
    from pathlib import Path

    assert ConverterRegistry({}).detect_content(Path("scan")) is None
