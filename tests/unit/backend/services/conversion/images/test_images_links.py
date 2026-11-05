"""Images in a folder next to the Markdown (feature 012, ADR-0033): links, names, the folder."""

import base64
import zipfile
from pathlib import Path

import pytest
from support import ODT_DIR
from support.images_cases import detection, png

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import ExtractedImage
from clearmd.backend.services.conversion import images
from clearmd.backend.services.conversion.images import ImageSink, epub_images, take_data_images
from clearmd.backend.use_cases.output_files import UnsafeOutput, write_images


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
