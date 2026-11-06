"""The installer's pictures (packaging/installer/images) are exactly what the script draws
(feature 019, ADR-0041): never edited by hand, never out of date."""

import hashlib

import pytest
from gui import make_installer_images
from gui.drawing.canvas import FONT, FONT_SHA256
from gui.drawing.installer import image_names


def _same_font() -> bool:
    return FONT.exists() and hashlib.sha256(FONT.read_bytes()).hexdigest() == FONT_SHA256


@pytest.mark.skipif(not _same_font(), reason="the letters are drawn with the dev container's font")
def test_the_committed_pictures_match_the_script() -> None:
    drawn = make_installer_images.files()
    stale = [n for n, d in drawn.items() if (make_installer_images.TARGET / n).read_bytes() != d]
    assert stale == [], "run: uv run python tests/gui/make_installer_images.py"


def test_no_picture_is_left_over() -> None:
    committed = {path.name for path in make_installer_images.TARGET.glob("*.png")}
    assert committed == set(image_names())  # names only: drawing needs the container's font
