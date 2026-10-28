"""The committed logo and icons are exactly what ClearMD's own script draws (ADR-0027)."""

from importlib.resources import files

import pytest
from gui import make_assets

from clearmd.frontend.presenter.icons import ICONS

ASSETS = files("clearmd.frontend") / "assets"

pytestmark = pytest.mark.skipif(
    not make_assets.FONT.exists(), reason="the icons' letters need the dev container's font"
)


def test_the_committed_assets_match_the_script() -> None:
    drawn = make_assets.assets()
    stale = [path for path, data in drawn.items() if (ASSETS / path).read_bytes() != data]
    assert stale == [], "run: uv run python tests/gui/make_assets.py"


def test_every_icon_the_presenter_names_exists_at_both_densities() -> None:
    for icon in ICONS:
        assert (ASSETS / "icons" / f"{icon}.png").is_file()
        assert (ASSETS / "icons" / f"{icon}@2x.png").is_file()
