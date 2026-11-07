"""Feature 018 — Choose (AC-02); spec/features/018_*/spec.md.

The flet window is built on a page that is not flet's (no screen), on the presenter's fake backend;
its pickers answer what the test sets.
"""

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest
from support.flet_acceptance import QUIET, Window, click, page_of, texts, windows
from support.gui_fakes import FakeBackend, MemoryBackend

from clearmd.backend.schemas.formats import EXTENSIONS
from clearmd.frontend.flet import FletApp
from clearmd.frontend.flet.visuals.images import asset_file
from clearmd.frontend.presenter.icons import ICONS
from clearmd.i18n import load_catalog


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def names(app: FletApp) -> list[str]:
    return [row.name for row in app.main.inputs.rows()]


def test_ac_02_add_files_add_folder_and_nothing_listed_twice(
    flet_window: Window, tmp_path: Path
) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    page = page_of(app)
    page.files = [str(tmp_path / "a.pdf"), str(tmp_path / "b.docx")]
    page.folder = str(tmp_path)
    click(app.main.add_files)
    click(app.main.add_folder)
    click(app.main.add_files)  # the same files again: never listed twice
    assert names(app) == ["a.pdf", "b.docx", f"{tmp_path.name}/"]
    assert [kind for kind, _title, _start in page.asked] == ["files", "folder", "files"]
    assert page.asked[0][1] == "Choose Documents" and page.asked[1][1] == "Choose a Folder"
    assert page.extensions == sorted(extension.lstrip(".") for extension in EXTENSIONS)
    page.files, page.folder = [], None  # both dialogs cancelled: nothing changes
    click(app.main.add_files)
    click(app.main.add_folder)
    assert len(names(app)) == 3


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_02_no_drop_on_the_window_the_empty_list_is_the_two_buttons(
    flet_window: Window, language: str
) -> None:
    app = flet_window(FakeBackend(settings=replace(QUIET, language=language)))
    catalog = load_catalog(language)
    start = app.main.start
    assert start.control.visible and not app.main.inputs.control.visible  # feature 021's tiles
    for tile, key in ((start.files, "gui.main.tile_files"), (start.folder, "gui.main.tile_folder")):
        assert tile.title.value == catalog.text(key)
    assert catalog.text("gui.main.drop") not in texts(app.root)  # no drop zone


def test_ac_02_the_list_is_numbered_with_an_icon_on_every_row(
    flet_window: Window, tmp_path: Path
) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path / "b.docx", tmp_path / "n.xyz"])
    lines = app.main.inputs.lines
    assert len(lines) == 3 and not app.main.start.control.visible
    for number, line in enumerate(lines, start=1):
        row = line.frame.content
        assert row is not None and str(number) in texts(row)
        assert asset_file(str(line.picture.src)).is_file()
    assert [str(line.picture.src) for line in lines] == [
        "icons/pdf@2x.png",
        "icons/docx@2x.png",
        "icons/unknown@2x.png",
    ]
    assert texts(app.main.inputs.header)[0] == "#"
    assert all(asset_file(f"icons/{name}@2x.png").is_file() for name in ICONS)


def test_ac_02_remove_selected_clear_all_and_deselect_all(
    flet_window: Window, tmp_path: Path
) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path / "b.pdf", tmp_path / "c.pdf"])
    inputs = app.main.inputs
    click(inputs.lines[0].frame)  # a click on a row checks its box
    assert inputs.lines[0].box is not None and inputs.lines[0].box.value is True
    box = inputs.lines[1].box
    assert box is not None
    click(box)  # and its box does the same
    assert [row.name for row in inputs.selected_rows()] == ["a.pdf", "b.pdf"]
    click(app.main.deselect)
    assert inputs.selected_rows() == [] and inputs.lines[0].box.value is False
    click(inputs.lines[0].frame)
    click(app.main.remove)
    assert names(app) == ["b.pdf", "c.pdf"]
    click(inputs.lines[0].frame)
    page_of(app).press("Delete")  # the keyboard does the same
    assert names(app) == ["c.pdf"]
    app.presenter.add_paths([tmp_path / "d.pdf"])
    page_of(app).press("a", ctrl=True)  # Ctrl+A checks them all
    assert len(inputs.selected_rows()) == 2
    click(app.main.clear)
    assert names(app) == [] and app.main.start.control.visible  # the two tiles again


def test_ac_02_the_output_next_to_the_originals_or_in_a_folder_is_remembered(
    flet_window: Window, tmp_path: Path
) -> None:
    out = tmp_path / "Resultados"
    out.mkdir()
    backend = MemoryBackend(QUIET)
    app = flet_window(backend)
    page = page_of(app)
    page.folder = str(out)
    assert app.main.output_mode() == "next_to"
    app.main.mode.choose("folder")  # a click on "In a folder I choose": the folder is asked
    assert app.presenter.output_folder == out and str(out) in str(app.main.output_label.value)
    assert backend.settings.last_output_folder == str(out)
    app.main.mode.choose("next_to")
    assert app.presenter.output_folder is None and app.main.output_mode() == "next_to"
    click(app.main.pick)  # "Choose Folder…", offering the folder of last time
    assert app.presenter.output_folder == out and app.main.output_mode() == "folder"
    assert page.asked[-1][2] == str(out)
    page.folder = None
    app.main.mode.choose("next_to")
    app.main.mode.choose("folder")  # the dialog is cancelled: the choice stays as it was
    assert app.main.output_mode() == "next_to" and app.presenter.output_folder is None
    again = flet_window(backend)
    assert again.presenter.settings.last_output_folder == str(out)  # the suggestion next time


def test_ac_02_the_summary_format_and_the_images_choice(flet_window: Window) -> None:
    backend = MemoryBackend(QUIET)
    app = flet_window(backend)
    assert app.main.summary.value == "markdown" and app.main.images.value == "omit"
    app.main.summary.choose("markdown_pdf")
    app.main.images.choose("folder")
    assert backend.settings.summary_format == "markdown_pdf"
    assert backend.settings.images == "folder"
    again = flet_window(backend)  # remembered
    assert again.main.summary.value == "markdown_pdf" and again.main.images.value == "folder"
    app.main.summary.choose("markdown")
    app.main.images.choose("omit")
    assert backend.settings.summary_format == "markdown" and backend.settings.images == "omit"


def test_ac_02_a_theme_change_keeps_the_selected_row(flet_window: Window, tmp_path: Path) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path / "b.pdf"])
    click(app.main.inputs.lines[1].frame)
    app.apply_theme("dark")
    assert app.shown.palette.mode == "dark"
    assert [row.name for row in app.main.inputs.selected_rows()] == ["b.pdf"]
