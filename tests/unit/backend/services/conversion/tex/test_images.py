"""Images linked so that they work from the output .md (AC-13)."""

import shutil
from pathlib import Path

import pytest
from support import TEX_DIR

from clearmd.backend.services.conversion.tex.document import convert_document
from clearmd.backend.services.conversion.tex.images import graphics_paths, image_link


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    (tmp_path / "img").mkdir()
    (tmp_path / "img" / "plot.png").write_bytes(b"png")
    (tmp_path / "img" / "photo.jpg").write_bytes(b"jpg")
    (tmp_path / "figs").mkdir()
    (tmp_path / "figs" / "chart.pdf").write_bytes(b"pdf")
    return tmp_path


def _target(folder: Path) -> Path:
    return folder / "ClearMD_Output" / "OutputMD" / "main.md"


@pytest.mark.parametrize(
    ("argument", "expected"),
    [
        ("img/plot.png", "../../img/plot.png"),
        ("img/plot", "../../img/plot.png"),  # the extension is looked up
        ("img/photo", "../../img/photo.jpg"),
        ("chart", "../../figs/chart.pdf"),  # through \graphicspath
        ("plot", "../../img/plot.png"),
    ],
)
def test_the_link_works_from_the_output_file(folder: Path, argument: str, expected: str) -> None:
    assert image_link(argument, folder, ["img/", "figs/"], _target(folder)) == expected


@pytest.mark.parametrize("argument", ["missing", "img/missing.png", "/etc/hosts", "../img/plot"])
def test_a_missing_or_outside_image_keeps_the_path_as_written(folder: Path, argument: str) -> None:
    assert image_link(argument, folder, [], _target(folder)) == argument


def test_an_image_through_a_link_is_not_looked_up(
    folder: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    outside = tmp_path_factory.mktemp("outside") / "secret.png"
    outside.write_bytes(b"png")
    (folder / "img" / "linked.png").symlink_to(outside)
    assert image_link("img/linked", folder, [], _target(folder)) == "img/linked"


def test_spaces_are_wrapped_so_the_link_stays_valid(folder: Path) -> None:
    (folder / "img" / "my plot.png").write_bytes(b"png")
    assert image_link("img/my plot", folder, [], _target(folder)) == "<../../img/my plot.png>"


def test_graphicspath_is_read_from_the_source() -> None:
    assert graphics_paths("\\graphicspath{{img/}{figs/}}") == ["img/", "figs/"]
    assert graphics_paths("% \\graphicspath{{no/}}\nnada") == []


def test_the_thesis_figure_links_through_its_graphicspath(tmp_path: Path) -> None:
    shutil.copytree(TEX_DIR / "thesis", tmp_path / "thesis")
    main = tmp_path / "thesis" / "main.tex"
    text = convert_document(main, _target(main.parent)).markdown
    assert "![Desde graphicspath](../../img/plot.png)" in text
