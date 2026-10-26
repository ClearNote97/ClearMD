"""Images stay inside the .odt: placeholders with their title, and a note (AC-10)."""

from pathlib import Path

from build_fixtures import ODT_IMAGES_BODY, _odt_styles, _odt_xml, odt_package, tiny_png
from support import ODT_DIR

from clearmd.backend.schemas.notes import NoteItem, NoteKind
from clearmd.backend.services.conversion.odt import OdtConverter


def convert(path: Path) -> tuple[str, dict[NoteKind, tuple[NoteItem, ...]]]:
    result = OdtConverter().convert(path, None, path.with_suffix(".md"))  # type: ignore[arg-type]
    return result.markdown, {note.kind: note.items for note in result.notes}


def _with_language(language: str) -> bytes:
    styles = _odt_styles().replace(
        b"<office:styles>",
        b'<office:styles><style:default-style style:family="paragraph">'
        b'<style:text-properties fo:language="' + language.encode() + b'" fo:country="CO"/>'
        b"</style:default-style>",
    )
    return odt_package(
        _odt_xml("document-content", ODT_IMAGES_BODY),
        extra={"styles.xml": styles, "Pictures/map.png": tiny_png()},
    )


def test_each_image_becomes_a_placeholder_with_its_title_and_is_counted() -> None:
    markdown, found = convert(ODT_DIR / "images.odt")
    assert "*Image: Mapa de la región*" in markdown
    assert "*Image: Una descripción*" in markdown
    assert "*Image: Logo*" in markdown
    assert found[NoteKind.IMAGES_NOT_EXTRACTED] == (NoteItem("3"),)
    assert NoteKind.ELEMENTS_SIMPLIFIED not in found


def test_the_placeholder_speaks_the_documents_language(tmp_path: Path) -> None:
    path = tmp_path / "es.odt"
    path.write_bytes(_with_language("es"))
    markdown, _ = convert(path)
    assert "*Imagen: Mapa de la región*" in markdown


def test_a_formulas_replacement_picture_is_not_an_image() -> None:
    _, found = convert(ODT_DIR / "real" / "report.odt")
    assert found[NoteKind.IMAGES_NOT_EXTRACTED] == (NoteItem("1"),)  # the green dot only


def test_an_image_title_never_becomes_markdown(tmp_path: Path) -> None:
    body = (
        '<text:p><draw:frame><draw:image xlink:href="Pictures/x.png"/>'
        "<svg:title>x](http://evil.example/b.png) &lt;img src=y&gt;</svg:title>"
        "</draw:frame></text:p>"
    )
    path = tmp_path / "t.odt"
    path.write_bytes(odt_package(_odt_xml("document-content", body)))
    markdown, _ = convert(path)
    assert "](" not in markdown and "<img" not in markdown


def test_a_framed_caption_keeps_its_text_and_its_image(tmp_path: Path) -> None:
    body = (
        '<text:p><draw:frame draw:name="Marco"><draw:text-box><text:p>'
        '<draw:frame draw:name="Foto"><draw:image xlink:href="Pictures/x.png"/>'
        "<svg:title>Foto</svg:title></draw:frame>Figura 1: el río</text:p></draw:text-box>"
        "</draw:frame></text:p>"
    )
    path = tmp_path / "t.odt"
    path.write_bytes(odt_package(_odt_xml("document-content", body)))
    markdown, found = convert(path)
    assert "*Image: Foto*" in markdown and "Figura 1: el río" in markdown
    assert found[NoteKind.IMAGES_NOT_EXTRACTED] == (NoteItem("1"),)


def test_a_linked_image_is_still_a_placeholder_and_never_a_link(tmp_path: Path) -> None:
    body = (
        '<text:p><draw:a xlink:href="http://evil.example/"><draw:frame>'
        '<draw:image xlink:href="Pictures/x.png"/><svg:title>T</svg:title></draw:frame>'
        "</draw:a></text:p>"
    )
    path = tmp_path / "t.odt"
    path.write_bytes(odt_package(_odt_xml("document-content", body)))
    markdown, found = convert(path)
    assert "*Image: T*" in markdown and "](" not in markdown
    assert NoteKind.ELEMENTS_SIMPLIFIED not in found
