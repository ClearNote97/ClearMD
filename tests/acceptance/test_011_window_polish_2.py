"""Feature 011 — one test per acceptance criterion (spec/features/011_*/spec.md)."""

import time
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from PIL import Image
from support.gui_close import shut
from support.gui_fakes import FakeBackend

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.ttk import TtkApp, art
from clearmd.frontend.ttk.brand import LIGHT
from clearmd.i18n import load_catalog

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def app(display: str) -> Iterator[TtkApp]:
    window = TtkApp(FakeBackend(settings=Settings(show_welcome=False, theme="light")))
    window.start()
    pump(window, seconds=0.5)
    yield window
    shut(window)


def pump(app: TtkApp, *, until: Callable[[], bool] | None = None, seconds: float = 1.0) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        app.root.update()
        if until is not None and until():
            return
        time.sleep(0.01)


def test_ac_01_settings_and_help_are_sections_of_the_rail(app: TtkApp) -> None:
    rail, settings, help_ = app.rail, app.rail.settings, app.rail.help
    assert settings.winfo_height() == 44 == help_.winfo_height()
    assert settings.winfo_width() == help_.winfo_width() == rail.winfo_width() - 2 * 16
    assert settings.cget("text") == "Settings" and help_.cget("text") == "Help"
    padding = app.style.lookup(str(settings.cget("style")), "padding")
    assert str(padding[0]) == "40"  # with the face's border: where a step's word starts
    app.root.geometry("900x600")  # the compact rail: the marks alone, centred
    pump(app, until=lambda: rail._compact)
    pump(app, seconds=0.3)
    assert settings.cget("text") == "⚙" and help_.cget("text") == "?"
    assert "Compact" in str(settings.cget("style"))


def test_ac_02_the_shape_is_whole_in_the_header_and_the_page_is_outlined(app: TtkApp) -> None:
    band = 110
    picture = art.surface(600, 400, LIGHT.ground, LIGHT.shape, band=band).convert("RGB")
    ground = Image.new("RGB", (1, 1), LIGHT.ground).getpixel((0, 0))
    assert all(picture.getpixel((x, band)) == ground for x in range(300, 600))

    def outlines() -> list[int]:
        return [i for i in app.surface.find_all() if str(app.surface.type(i)) == "polygon"]

    assert len(outlines()) == 1  # drawn on the canvas: it follows a resize at once
    app.root.geometry("920x620")
    app.root.update()
    x1, y1, x2, y2 = app.surface.bbox(outlines()[0])
    assert x2 >= app.surface.winfo_width() - 20


def test_ac_02_the_lists_keep_their_rows_at_the_smallest_window(
    app: TtkApp, tmp_path: Path
) -> None:
    app.root.geometry("800x600")  # the smallest window (its minimum since feature 011)
    app.presenter.add_paths([tmp_path / f"{n}.pdf" for n in range(6)])
    pump(app, seconds=0.5)
    tree = app.main.inputs.tree
    assert app.root.minsize() == (800, 600)
    # Its heading and a row at least (two with Linux's fonts; Segoe UI is taller: one, CI).
    assert tree.winfo_ismapped() and tree.winfo_height() > 55


def test_ac_03_every_page_says_what_is_missing_and_never_cut(app: TtkApp) -> None:
    for page in (2, 3, 4):
        app.presenter.go_to(page)
        assert app.actions.hint.cget("text").startswith("Nothing chosen yet")
    app.presenter.add_paths([Path("/docs")])
    app.presenter.go_to(2)
    assert app.actions.hint.cget("text") == "Press Next on Choose to see what will happen."
    app.root.geometry("800x600")
    pump(app, seconds=0.3)
    wrap = int(str(app.actions.hint.cget("wraplength")) or 0)
    assert 0 < wrap <= app.actions.hint.winfo_width()  # a long hint takes two lines
    spanish = load_catalog("es")
    assert spanish.text("gui.nav.need_inputs_first") and spanish.text("gui.nav.nothing_written")


def test_ac_04_screenshots_in_both_themes_and_languages() -> None:
    shots = ROOT / "docs" / "screenshots" / "011"
    for screen in ("1-choose", "3-convert-ready", "1-choose-compact", "1-choose-empty"):
        for theme in ("light", "dark"):
            for language in ("en", "es"):
                assert (shots / f"{screen}-{theme}-{language}.png").is_file(), screen
