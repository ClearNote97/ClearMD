"""Images kept in a folder next to the Markdown (feature 012, ADR-0033)."""

import base64
import io
import zipfile
from pathlib import Path

import pytest
from PIL import Image
from support import ODT_DIR

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod, ExtractedImage
from clearmd.backend.services.conversion import images
from clearmd.backend.services.conversion.images import ImageSink, epub_images, take_data_images
from clearmd.backend.use_cases.output_files import UnsafeOutput, write_images


def png(colour: str = "red", size: tuple[int, int] = (60, 40)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, colour).save(buffer, "PNG")
    return buffer.getvalue()


def detection(format_id: FormatId) -> Detection:
    return Detection(format_id, DetectionMethod.EXTENSION)


# --- The sink ----------------------------------------------------------------------------------


def test_the_sink_names_checks_and_links() -> None:
    sink = ImageSink.for_folder("report_images")
    assert sink.add(png()) == "report_images/image-001.png"
    assert sink.add(b"\xff\xd8\xff" + b"\x00" * 100) == "report_images/image-002.jpg"
    assert sink.add(b"<svg onload='x'>" + b" " * 100) is None  # not a picture a viewer shows
    assert sink.add(b"\x89PNG") is None  # too small to be one
    assert [image.name for image in sink.images] == ["image-001.png", "image-002.jpg"]
    assert sink.left_out == 1
    assert sink.add(png()) == "report_images/image-001.png"  # the same picture: the same file


def test_the_sink_keeps_its_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(images, "MAX_IMAGES", 2)
    sink = ImageSink.for_folder("x_images")
    links = [sink.add(png(colour)) for colour in ("red", "green", "blue")]  # three pictures
    assert links[2] is None and sink.left_out == 1


def test_data_images_become_files_and_the_rest_stays() -> None:
    data = base64.b64encode(png()).decode()
    markdown = f"Before ![a map](data:image/png;base64,{data}) after"
    sink = ImageSink.for_folder("doc_images")
    assert take_data_images(markdown, sink) == "Before ![a map](doc_images/image-001.png) after"
    assert take_data_images(markdown, None) == markdown


def test_an_epub_picture_is_read_from_its_package(tmp_path: Path) -> None:
    book = tmp_path / "book.epub"
    with zipfile.ZipFile(book, "w") as package:
        package.writestr("mimetype", "application/epub+zip")
        package.writestr("OEBPS/images/map.png", png())
    sink = ImageSink.for_folder("book_images")
    markdown = epub_images(book, "![Map](../images/map.png) ![x](http://e/x.png)", sink)
    assert markdown == "![Map](book_images/image-001.png) ![x](http://e/x.png)"


# --- The converters ----------------------------------------------------------------------------


def test_a_pptx_picture_goes_to_the_folder(tmp_path: Path) -> None:
    import pptx
    from pptx.util import Inches

    from clearmd.backend.services.conversion.markitdown_adapter import MarkItDownConverter

    picture = tmp_path / "red.png"
    picture.write_bytes(png())
    deck = pptx.Presentation()
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    slide.shapes.add_picture(str(picture), Inches(1), Inches(1))
    source = tmp_path / "deck.pptx"
    deck.save(str(source))
    sink = ImageSink.for_folder("deck_images")
    result = MarkItDownConverter().convert(
        source, detection(FormatId.PPTX), tmp_path / "deck.md", images=sink
    )
    assert "](deck_images/image-001.png)" in result.markdown
    assert len(sink.images) == 1


def test_an_odt_picture_goes_to_the_folder(tmp_path: Path) -> None:
    from clearmd.backend.services.conversion.odt import OdtConverter

    sink = ImageSink.for_folder("images_images")
    result = OdtConverter().convert(
        ODT_DIR / "images.odt", detection(FormatId.ODT), tmp_path / "x.md", images=sink
    )
    without = OdtConverter().convert(
        ODT_DIR / "images.odt", detection(FormatId.ODT), tmp_path / "x.md"
    )
    assert "*Image: Mapa de la región*" in without.markdown  # off: the placeholder, as before
    assert "![Mapa de la región](images_images/image-001.png)" in result.markdown
    assert len(sink.images) == 1  # used three times, kept once


def test_a_pdf_picture_is_placed_where_it_stands(tmp_path: Path) -> None:
    from clearmd.backend.services.conversion.pdf import PdfConverter

    source = tmp_path / "scan.pdf"
    Image.new("RGB", (300, 200), "blue").save(source, "PDF")
    sink = ImageSink.for_folder("scan_images")
    result = PdfConverter().convert(source, detection(FormatId.PDF), tmp_path / "s.md", images=sink)
    assert "![](scan_images/image-001.png)" in result.markdown
    assert sink.images and sink.images[0].data.startswith(b"\x89PNG")
    off = PdfConverter().convert(source, detection(FormatId.PDF), tmp_path / "s.md")
    assert "scan_images" not in off.markdown


# --- Writing them ------------------------------------------------------------------------------


def test_images_are_written_and_old_ones_go(tmp_path: Path) -> None:
    root = tmp_path / "ClearMD_Output"
    folder = root / "OutputMD" / "report_images"
    folder.mkdir(parents=True)
    (folder / "image-009.png").write_bytes(b"old")
    (folder / "notes.txt").write_text("the user's own file", encoding="utf-8")
    write_images(folder, [ExtractedImage("image-001.png", png())], inside=root)
    assert sorted(path.name for path in folder.iterdir()) == ["image-001.png", "notes.txt"]


def test_an_image_name_from_elsewhere_is_refused(tmp_path: Path) -> None:
    root = tmp_path / "ClearMD_Output"
    with pytest.raises(UnsafeOutput):
        write_images(root / "x_images", [ExtractedImage("../evil.png", png())], inside=root)


def test_a_planted_link_as_the_folder_is_never_followed(tmp_path: Path) -> None:
    root = tmp_path / "ClearMD_Output"
    (root / "OutputMD").mkdir(parents=True)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (root / "OutputMD" / "x_images").symlink_to(elsewhere)
    with pytest.raises(UnsafeOutput):
        write_images(
            root / "OutputMD" / "x_images", [ExtractedImage("image-001.png", png())], inside=root
        )
    assert list(elsewhere.iterdir()) == []
