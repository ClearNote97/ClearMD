"""Feature 021 — flet's empty list as two large tiles (spec/features/021_*/spec.md): the flet
window on a page that is not flet's, on the presenter's fake backend."""

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import flet as ft
import pytest
from support.flet_acceptance import QUIET, Window, click, page_of, windows
from support.gui_fakes import FakeBackend

from clearmd.frontend.flet import FletApp
from clearmd.frontend.flet.window.controls import apply_enabled
from clearmd.frontend.presenter import Action
from clearmd.i18n import load_catalog

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def names(app: FletApp) -> list[str]:
    return [row.name for row in app.main.inputs.rows()]


def shown(app: FletApp) -> dict[str, bool]:
    return {
        "tiles": bool(app.main.start.control.visible),
        "buttons": bool(app.main.entry.visible),
        "list": bool(app.main.inputs.control.visible),
        "links": bool(app.main.editing.visible),
    }


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_01_nothing_listed_the_two_tiles_alone(flet_window: Window, language: str) -> None:
    app = flet_window(FakeBackend(settings=replace(QUIET, language=language)))
    catalog = load_catalog(language)
    start = app.main.start
    assert shown(app) == {"tiles": True, "buttons": False, "list": False, "links": False}
    for tile, title, body in (
        (start.files, "gui.main.add_files", "gui.main.start_files"),
        (start.folder, "gui.main.add_folder", "gui.main.start_folder"),
    ):
        assert isinstance(tile.icon, ft.Icon) and tile.icon.icon is not None
        assert tile.title.value == catalog.text(title)
        assert tile.body.value == catalog.text(body)
    assert start.hint.value == catalog.text("gui.main.start_hint")


def test_ac_02_each_tile_does_what_its_button_does(flet_window: Window, tmp_path: Path) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    page = page_of(app)
    page.files = [str(tmp_path / "a.pdf")]
    click(app.main.start.files.control)
    assert names(app) == ["a.pdf"]
    app.presenter.clear_inputs()
    page.folder = str(tmp_path)
    click(app.main.start.folder.control)
    assert names(app) == [f"{tmp_path.name}/"]
    assert [kind for kind, _title, _start in page.asked] == ["files", "folder"]


def test_ac_03_the_tiles_give_way_to_the_list_and_come_back(
    flet_window: Window, tmp_path: Path
) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    app.presenter.add_paths([tmp_path / "a.pdf"])
    assert shown(app) == {"tiles": False, "buttons": True, "list": True, "links": True}
    click(app.main.clear)
    assert names(app) == []
    assert shown(app) == {"tiles": True, "buttons": False, "list": False, "links": False}


def test_ac_04_the_tiles_follow_the_small_buttons(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    tiles = (app.main.start.files.control, app.main.start.folder.control)
    apply_enabled(set(), app.main, app.rail)
    assert all(tile.disabled for tile in tiles) and app.main.add_files.disabled
    apply_enabled({Action.ADD}, app.main, app.rail)
    assert not any(tile.disabled for tile in tiles) and not app.main.add_files.disabled


def test_ac_05_their_texts_in_both_languages() -> None:
    for language in ("en", "es"):
        text = (ROOT / "src" / "clearmd" / "i18n" / f"{language}.toml").read_text(encoding="utf-8")
        for key in ("start_files", "start_folder", "start_hint"):
            assert f"\n{key} = " in text
        assert "empty_use_buttons" not in text
