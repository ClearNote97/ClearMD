"""The committed logo and icons are exactly what ClearMD's own script draws (ADR-0027)."""

import hashlib
from importlib.resources import files

import pytest
from gui import make_assets
from gui.drawing.canvas import FONT, FONT_SHA256

from clearmd.frontend.presenter.icons import ICONS

ASSETS = files("clearmd.frontend") / "assets"


def _same_font() -> bool:
    if not FONT.exists():
        return False
    return hashlib.sha256(FONT.read_bytes()).hexdigest() == FONT_SHA256


@pytest.mark.skipif(
    not _same_font(), reason="the icons' letters are drawn with the dev container's font"
)
def test_the_committed_assets_match_the_script() -> None:
    drawn = make_assets.assets()
    stale = [path for path, data in drawn.items() if (ASSETS / path).read_bytes() != data]
    assert stale == [], "run: uv run python tests/gui/make_assets.py"


def test_every_icon_the_presenter_names_exists_at_both_densities() -> None:
    for icon in ICONS:
        assert (ASSETS / "icons" / f"{icon}.png").is_file()
        assert (ASSETS / "icons" / f"{icon}@2x.png").is_file()
