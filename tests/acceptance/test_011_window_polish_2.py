"""Feature 011 — one test per acceptance criterion (spec/features/011_*/spec.md)."""

import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from PIL import Image
from support.gui_close import shut
from support.gui_fakes import FakeBackend

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.ttk import TtkApp, art
from clearmd.frontend.ttk.brand import LIGHT

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def app(display: str) -> Iterator[TtkApp]:
    window = TtkApp(FakeBackend(settings=Settings(show_welcome=False, theme="light")))
    window.start()
    deadline = time.monotonic() + 0.5
    while time.monotonic() < deadline:
        window.root.update()
        time.sleep(0.01)
    yield window
    shut(window)


def test_ac_01_settings_and_help_are_sections_of_the_rail(app: TtkApp) -> None:
    settings, help_ = app.rail.settings, app.rail.help
    step_band = app.rail.winfo_width() - 2 * 8  # the rail's width less its gaps, as a step's
    assert (
        settings.winfo_width() >= step_band - 24 and help_.winfo_width() == settings.winfo_width()
    )
    assert settings.winfo_height() == 44 == help_.winfo_height()
    assert settings.cget("text").startswith("⚙") and help_.cget("text").startswith("?")
    assert help_.cget("text").count("?") == 1


def test_ac_02_the_shape_is_whole_in_the_header_and_the_page_is_outlined() -> None:
    band = 110
    picture = art.surface(600, 400, LIGHT.ground, LIGHT.shape, band=band, box=(8, band, 584, 384),
                          border=LIGHT.border)  # fmt: skip
    ground = Image.new("RGB", (1, 1), LIGHT.ground).getpixel((0, 0))
    row = [picture.convert("RGB").getpixel((x, band + 6)) for x in range(400, 570)]
    assert all(pixel == ground for pixel in row)  # nothing of the shape under the band
    assert picture.convert("RGB").getpixel((300, band)) != ground  # the card's outline


def test_ac_03_every_page_says_what_is_missing(app: TtkApp) -> None:
    for page in (2, 3, 4):
        app.presenter.go_to(page)
        assert app.actions.hint.cget("text").startswith("Nothing chosen yet")
    app.presenter.add_paths([Path("/docs")])
    app.presenter.go_to(2)
    assert app.actions.hint.cget("text") == "Press Next on Choose to see what will happen."


def test_ac_04_screenshots_in_both_themes_and_languages() -> None:
    shots = ROOT / "docs" / "screenshots" / "011"
    for screen in ("1-choose", "3-convert-ready", "1-choose-compact", "1-choose-empty"):
        for theme in ("light", "dark"):
            for language in ("en", "es"):
                assert (shots / f"{screen}-{theme}-{language}.png").is_file(), screen
