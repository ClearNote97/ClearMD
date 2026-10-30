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


# --- Review of 012 -----------------------------------------------------------------------------


def pdf_drawing(draws: str, *, side: int = 2) -> bytes:
    """A PDF page drawing one small RGB image with ``draws`` (its "cm" and "Do" operators)."""
    pixels = bytes([255, 0, 0]) * side * side
    page = f"BT /F1 12 Tf 72 700 Td (Hello) Tj ET {draws}".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R"
        b" >> /XObject << /Im0 5 0 R >> >> /Contents 6 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceRGB"
        b" /BitsPerComponent 8 /Length %d >>\nstream\n"
        % (side, side, len(pixels))
        + pixels
        + b"\nendstream",
        b"<< /Length %d >>\nstream\n" % len(page) + page + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        xref,
    )
    return bytes(out)


def pdf_pictures(tmp_path: Path, data: bytes) -> ImageSink:
    from clearmd.backend.services.conversion.pdf import PdfConverter

    source = tmp_path / "p.pdf"
    source.write_bytes(data)
    sink = ImageSink.for_folder("p_images")
    PdfConverter().convert(source, detection(FormatId.PDF), tmp_path / "p.md", images=sink)
    return sink


def test_a_small_picture_drawn_huge_is_kept_at_its_own_size(tmp_path: Path) -> None:
    sink = pdf_pictures(tmp_path, pdf_drawing("q 12000 0 0 12000 0 0 cm /Im0 Do Q"))
    assert Image.open(io.BytesIO(sink.images[0].data)).size == (2, 2)  # not 12000 x 12000


def test_a_large_picture_drawn_small_keeps_its_pixels(tmp_path: Path) -> None:
    sink = pdf_pictures(tmp_path, pdf_drawing("q 60 0 0 40 72 300 cm /Im0 Do Q", side=300))
    assert Image.open(io.BytesIO(sink.images[0].data)).size == (300, 300)


def test_a_document_has_a_budget_of_pixels(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from clearmd.backend.services.conversion.pdf import reader

    monkeypatch.setattr(reader, "MAX_DOCUMENT_PIXELS", 3)
    sink = pdf_pictures(tmp_path, pdf_drawing("q 100 0 0 100 72 300 cm /Im0 Do Q"))
    assert sink.images == [] and sink.left_out == 1


def test_a_picture_inside_a_form_is_found(tmp_path: Path) -> None:
    form = b"q 100 0 0 100 0 0 cm /Im0 Do Q"
    data = pdf_drawing("/Fm0 Do")
    data = data.replace(
        b"/XObject << /Im0 5 0 R >>", b"/XObject << /Im0 5 0 R /Fm0 7 0 R >>"
    ).replace(
        b"xref",
        b"7 0 obj\n<< /Type /XObject /Subtype /Form /BBox [0 0 200 200] /Resources << /XObject <<"
        b" /Im0 5 0 R >> >> /Length %d >>\nstream\n"
        % len(form)
        + form
        + b"\nendstream\nendobj\nxref",
    )
    assert len(pdf_pictures(tmp_path, data).images) == 1


def test_an_alt_with_brackets_or_a_title_still_gives_a_file() -> None:
    data = base64.b64encode(png()).decode()
    sink = ImageSink.for_folder("d_images")
    markdown = take_data_images(
        f'![Fig. [1] map](data:image/png;base64,{data}) ![b](data:image/png;base64,{data} "T")',
        sink,
    )
    assert "base64" not in markdown and markdown.count("](d_images/image-001.png)") == 2


def test_a_data_link_no_image_takes_is_cut_and_counted() -> None:
    data = base64.b64encode(png()).decode()
    sink = ImageSink.for_folder("d_images")
    markdown = take_data_images(f"[see](data:image/png;base64,{data})", sink)
    assert markdown == "[see](data:image/png;base64...)" and sink.left_out == 1


def test_epub_pictures_with_one_name_in_two_folders(tmp_path: Path) -> None:
    book = tmp_path / "b.epub"
    with zipfile.ZipFile(book, "w") as package:
        package.writestr("OEBPS/ch1/fig.png", png("red"))
        package.writestr("OEBPS/ch2/fig.png", png("blue"))
        package.writestr("OEBPS/x/same.png", png("green"))
        package.writestr("OEBPS/y/same.png", png("white"))
    sink = ImageSink.for_folder("b_images")
    markdown = epub_images(book, "![r](../ch1/fig.png) ![b](../ch2/fig.png) ![s](same.png)", sink)
    assert markdown == "![r](b_images/image-001.png) ![b](b_images/image-002.png) ![s](same.png)"


def test_a_folder_name_with_hash_percent_or_question_mark_links_to_itself() -> None:
    assert ImageSink.for_folder("Q#3 100% what?_images").add(png()) == (
        "Q%233 100%25 what%3F_images/image-001.png"
    )


def test_bm_alone_is_no_bitmap() -> None:
    assert images.kind(b"BM" + b"\x00" * 100) is None
    header = b"BM" + b"\x00" * 12 + (40).to_bytes(4, "little")
    assert images.kind(header + b"\x00" * 100) == "bmp"


def test_an_odt_picture_kept_is_not_told_as_left_inside(tmp_path: Path) -> None:
    from clearmd.backend.services.conversion.odt import OdtConverter

    sink = ImageSink.for_folder("i_images")
    result = OdtConverter().convert(
        ODT_DIR / "images.odt", detection(FormatId.ODT), tmp_path / "x.md", images=sink
    )
    assert [note.kind.value for note in result.notes if "image" in note.kind.value] == []


def test_pictures_written_first_and_an_empty_folder_goes(tmp_path: Path) -> None:
    root = tmp_path / "ClearMD_Output"
    folder = root / "OutputMD" / "r_images"
    folder.mkdir(parents=True)
    (folder / "image-001.png").write_bytes(b"old")
    with pytest.raises(UnsafeOutput):  # every name checked before anything changes
        write_images(
            folder,
            [ExtractedImage("image-001.png", png()), ExtractedImage("x", png())],
            inside=root,
        )
    assert (folder / "image-001.png").read_bytes() == b"old"
    write_images(folder, [], inside=root)
    assert not folder.exists()
