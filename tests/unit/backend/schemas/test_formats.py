from clearmd.backend.schemas import formats
from clearmd.backend.schemas.formats import FormatId


def test_every_format_has_an_extension() -> None:
    assert set(formats.EXTENSIONS.values()) == set(FormatId)


def test_extensions_are_lowercase_and_dotted() -> None:
    assert all(ext.startswith(".") and ext == ext.lower() for ext in formats.EXTENSIONS)


def test_format_for_extension_ignores_case_and_rejects_unknown() -> None:
    assert formats.format_for_extension(".PDF") is FormatId.PDF
    assert formats.format_for_extension(".htm") is FormatId.HTML
    assert formats.format_for_extension(".tex") is None
    assert formats.format_for_extension("") is None


def test_zip_based_formats() -> None:
    assert formats.ZIP_BASED == {FormatId.DOCX, FormatId.PPTX, FormatId.XLSX, FormatId.EPUB}


def test_skip_only_extensions_are_not_convertible() -> None:
    skip_only = formats.MARKDOWN_EXTENSIONS | formats.ZIP_EXTENSIONS
    assert skip_only.isdisjoint(formats.EXTENSIONS)


def test_output_names_follow_adr_0016() -> None:
    assert formats.OUTPUT_DIR_NAME == "ClearMD_Output"
    assert formats.RESULTS_DIR_NAME == "OutputMD"
    assert formats.SUMMARY_NAME == "Resumen_ClearMD.md"
