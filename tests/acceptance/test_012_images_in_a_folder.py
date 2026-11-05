"""Feature 012 — one test per acceptance criterion (spec/features/012_*/spec.md): real batches
through the command line."""

import io
import shutil
import time
import zipfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from PIL import Image
from support import DOCUMENTS_DIR, ODT_DIR
from support.gui_close import shut
from support.gui_fakes import FakeBackend

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.cli import main
from clearmd.frontend.ttk import TtkApp

ROOT = Path(__file__).resolve().parents[2]


def picture(colour: str = "red") -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (80, 50), colour).save(buffer, "PNG")
    return buffer.getvalue()


_W = "http://schemas.openxmlformats.org"
_DOCX_PARTS = {
    "[Content_Types].xml": (
        '<Types xmlns="' + _W + '/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
        'relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
        '<Default Extension="png" ContentType="image/png"/><Override PartName="/word/document.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.'
        'main+xml"/></Types>'
    ),
    "_rels/.rels": (
        '<Relationships xmlns="' + _W + '/package/2006/relationships"><Relationship Id="rId1" '
        'Type="' + _W + '/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/></Relationships>'
    ),
    "word/_rels/document.xml.rels": (
        '<Relationships xmlns="' + _W + '/package/2006/relationships"><Relationship Id="rIdImg" '
        'Type="' + _W + '/officeDocument/2006/relationships/image" Target="media/image1.png"/>'
        "</Relationships>"
    ),
    "word/document.xml": (
        '<w:document xmlns:w="'
        + _W
        + '/wordprocessingml/2006/main" xmlns:r="'
        + _W
        + '/officeDocument/2006/relationships" xmlns:wp="'
        + _W
        + '/drawingml/2006/wordprocessingDrawing" xmlns:a="'
        + _W
        + '/drawingml/2006/main" '
        'xmlns:pic="' + _W + '/drawingml/2006/picture"><w:body><w:p><w:r><w:t>Hello</w:t></w:r>'
        '</w:p><w:p><w:r><w:drawing><wp:inline><wp:extent cx="914400" cy="914400"/><wp:docPr '
        'id="1" name="Picture 1" descr="A map"/><a:graphic><a:graphicData uri="'
        + _W
        + '/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="x"/>'
        '<pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="rIdImg"/></pic:blipFill>'
        "<pic:spPr/></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>"
        "</w:body></w:document>"
    ),
}


def docx(path: Path) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as package:
        for name, text in _DOCX_PARTS.items():
            package.writestr(name, text)
        package.writestr("word/media/image1.png", picture("green"))


def epub(path: Path) -> None:
    container = (
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" '
        'media-type="application/oebps-package+xml"/></rootfiles></container>'
    )
    opf = (
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">x'
        "</dc:identifier><dc:title>Book</dc:title><dc:language>en</dc:language></metadata>"
        '<manifest><item id="c1" href="text/c1.xhtml" media-type="application/xhtml+xml"/>'
        '<item id="i1" href="images/map.png" media-type="image/png"/></manifest>'
        '<spine><itemref idref="c1"/></spine></package>'
    )
    chapter = (
        '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>One</title></head><body>'
        '<p>Chapter text.</p><img src="../images/map.png" alt="Map"/></body></html>'
    )
    with zipfile.ZipFile(path, "w") as package:
        package.writestr("mimetype", "application/epub+zip")
        package.writestr("META-INF/container.xml", container)
        package.writestr("OEBPS/content.opf", opf)
        package.writestr("OEBPS/text/c1.xhtml", chapter)
        package.writestr("OEBPS/images/map.png", picture("blue"))


def batch(workdir: Path) -> Path:
    import pptx
    from pptx.util import Inches

    docs = workdir / "docs"
    docs.mkdir()
    image = workdir / "red.png"
    image.write_bytes(picture())
    deck = pptx.Presentation()
    deck.slides.add_slide(deck.slide_layouts[6]).shapes.add_picture(
        str(image), Inches(1), Inches(1)
    )
    deck.save(str(docs / "deck.pptx"))
    Image.new("RGB", (300, 200), "blue").save(docs / "scan.pdf", "PDF")
    shutil.copyfile(ODT_DIR / "images.odt", docs / "report.odt")
    shutil.copyfile(DOCUMENTS_DIR / "sample.txt", docs / "notes.txt")
    docx(docs / "letter.docx")
    epub(docs / "book.epub")
    return docs


def output(workdir: Path) -> Path:
    return workdir / "ClearMD_Output" / "OutputMD" / "docs"


def test_ac_01_pictures_go_to_a_folder_next_to_the_markdown(workdir: Path) -> None:
    docs = batch(workdir)
    assert main([str(docs), "--quiet", "--images"]) == 0
    out = output(workdir)
    for name in ("deck", "scan", "report", "letter", "book"):
        markdown = (out / f"{name}.md").read_text(encoding="utf-8")
        assert f"]({name}_images/image-001.png)" in markdown, name
        assert (out / f"{name}_images" / "image-001.png").is_file(), name
    assert not (out / "notes_images").exists()  # no picture, no folder


def test_ac_01_the_suffix_follows_the_language(workdir: Path) -> None:
    docs = batch(workdir)
    main([str(docs), "--quiet", "--images", "--lang", "es"])
    assert (output(workdir) / "scan_imagenes" / "image-001.png").is_file()


def test_ac_02_by_default_no_picture_is_written(workdir: Path) -> None:
    docs = batch(workdir)
    main([str(docs), "--quiet"])
    out = output(workdir)
    assert not any(path.name.endswith("_images") for path in out.iterdir())
    for name in ("deck", "letter"):  # no data in a link either: markitdown's own short form
        assert "base64," not in (out / f"{name}.md").read_text(encoding="utf-8")
    assert "*Image: Mapa de la región*" in (out / "report.md").read_text(encoding="utf-8")


def test_ac_02_formats_that_keep_no_pictures_convert_with_the_folder_on(workdir: Path) -> None:
    """TeX and Excel keep no pictures: the folder must never make them fail (found in R01)."""
    docs = workdir / "docs"
    docs.mkdir()
    shutil.copyfile(DOCUMENTS_DIR / "sample.xlsx", docs / "sample.xlsx")
    (docs / "notes.tex").write_text("\\section{Notes}\nPlain text.\n", encoding="utf-8")
    assert main([str(docs), "--images", "--quiet", "--overwrite"]) == 0
    written = workdir / "ClearMD_Output" / "OutputMD" / "docs"
    assert (written / "sample.md").exists() and (written / "notes.md").exists()


def test_ac_03_a_picture_used_again_is_kept_once(workdir: Path) -> None:
    docs = batch(workdir)
    main([str(docs), "--quiet", "--images"])
    assert len(list((output(workdir) / "report_images").iterdir())) == 1  # used three times


def test_ac_04_earlier_pictures_are_replaced_and_a_link_is_never_followed(workdir: Path) -> None:
    docs = batch(workdir)
    main([str(docs), "--quiet", "--images"])
    folder = output(workdir) / "scan_images"
    (folder / "image-005.png").write_bytes(picture("green"))
    main([str(docs), "--quiet", "--images", "--overwrite"])
    assert sorted(path.name for path in folder.iterdir()) == ["image-001.png"]
    elsewhere = workdir / "elsewhere"
    elsewhere.mkdir()
    shutil.rmtree(folder)
    folder.symlink_to(elsewhere)
    main([str(docs), "--quiet", "--images", "--overwrite"])
    assert list(elsewhere.iterdir()) == []


@pytest.fixture
def app(display: str) -> Iterator[TtkApp]:
    window = TtkApp(FakeBackend(settings=Settings(show_welcome=False)))
    window.start()
    yield window
    shut(window)


def test_ac_05_the_choice_on_step_1_in_settings_and_the_cli(app: TtkApp) -> None:
    assert app.main.images.get() == "omit"
    folder_choice = next(b for b in app.main.summary_buttons if str(b.cget("value")) == "folder")
    folder_choice.invoke()
    assert app.presenter.settings.images == "folder"
    app.dialogs.show_settings()
    deadline = time.monotonic() + 2
    while app.dialog is None and time.monotonic() < deadline:
        app.root.update()
    assert app.dialog is not None and "images" in getattr(app.dialog, "values", {})
    app.dialog.close()
    shots = ROOT / "docs" / "screenshots" / "012"
    for theme in ("light", "dark"):
        for language in ("en", "es"):
            assert (shots / f"1-choose-{theme}-{language}.png").is_file()


def test_ac_05_the_choice_fits_the_smallest_window_in_spanish(display: str) -> None:
    window = TtkApp(FakeBackend(settings=Settings(show_welcome=False, language="es")))
    window.start()
    try:
        window.root.geometry("800x624")
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            window.root.update()
        last = window.main.summary_buttons[-1]  # "En una carpeta", the row's last choice
        # The output's card: the row's frame is in its heading, the heading in the card.
        card = window.root.nametowidget(last.winfo_parent().rsplit(".", 2)[0])
        assert last.winfo_ismapped()
        assert last.winfo_rootx() + last.winfo_width() <= card.winfo_rootx() + card.winfo_width()
    finally:
        shut(window)
