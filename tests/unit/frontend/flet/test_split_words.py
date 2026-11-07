"""Feature 024 in the flet window: the third cut, parts of about N words, on step 1 of Split and in
the settings' Split group; the hint under the note; Home's tiles anchored to the top; the empty
message line taking no room."""

from collections.abc import Iterator
from dataclasses import replace

import flet as ft
import pytest
from support.flet_acceptance import QUIET, Window, click, windows
from support.gui_fakes import FakeBackend

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.flet import FletApp
from clearmd.frontend.flet.views.dialogs.settings import SettingsDialog
from clearmd.i18n import load_catalog


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def split_window(flet_window: Window, settings: Settings = QUIET) -> tuple[FletApp, FakeBackend]:
    backend = FakeBackend(settings=settings)
    app = flet_window(backend)
    click(app.home.split.control)
    return app, backend


@pytest.mark.parametrize("language", ["en", "es"])
def test_the_third_cut_and_the_hint_come_from_the_catalog(
    flet_window: Window, language: str
) -> None:
    app, _backend = split_window(flet_window, replace(QUIET, language=language))
    catalog = load_catalog(language)
    split = app.main.split
    assert list(split.cut.radios) == ["parts", "pages", "words"]  # the order of the three windows
    assert split.cut.radios["words"].label == catalog.text("gui.split.words")
    assert split.words.field.value == "30000"
    assert split.note.value == catalog.text("gui.split.note")
    assert split.hint.value == catalog.text("gui.split.hint")
    assert split.cut.row.wrap  # a narrow window wraps the three cuts, never cuts them off
    pairs = split.cut.row.controls
    assert len(pairs) == 3 and all(isinstance(pair, ft.Row) for pair in pairs)
    unit = pairs[2]
    assert isinstance(unit, ft.Row) and isinstance(unit.controls[2], ft.Text)
    assert unit.controls[2].value == catalog.text("gui.split.words_unit")


def test_the_words_radio_and_field_call_choose_split(flet_window: Window) -> None:
    app, backend = split_window(flet_window)
    split = app.main.split
    split.cut.choose("words")
    assert backend.settings.split_cut == "words" and split.cut.value == "words"
    split.words.type("12000")
    assert backend.settings.split_words == 30_000  # nothing on a keystroke
    split.words.commit()
    assert backend.settings.split_words == 12_000 and split.words.field.value == "12000"


@pytest.mark.parametrize("typed", ["499", "0", "1000001", ""])
def test_a_refused_number_of_words_is_put_back(flet_window: Window, typed: str) -> None:
    app, backend = split_window(flet_window)
    words = app.main.split.words
    words.type(typed)
    words.commit()
    assert backend.settings.split_words == 30_000 and words.field.value == "30000"


def test_the_words_field_is_disabled_with_the_other_choices(flet_window: Window) -> None:
    app, _backend = split_window(flet_window)
    split = app.main.split
    assert not split.words.field.disabled
    split.set_disabled(True)
    assert split.words.field.disabled and split.cut.radios["words"].disabled


def test_the_settings_group_round_trips_the_words(flet_window: Window) -> None:
    app, backend = split_window(flet_window, replace(QUIET, split_words=8000))
    click(app.rail.settings)
    dialog = app.dialogs.current
    assert isinstance(dialog, SettingsDialog)
    group = dialog.split
    assert group.words.value == "8000"
    assert group.radios["words"].label == load_catalog("en").text("gui.settings.split_words")
    group.cut.value, group.words.value = "words", "50000"
    dialog.save()
    assert (backend.settings.split_cut, backend.settings.split_words) == ("words", 50_000)
    assert app.main.split.words.field.value == "50000"
    click(app.rail.settings)
    dialog = app.dialogs.current
    assert isinstance(dialog, SettingsDialog)
    dialog.split.words.value = "100"  # out of its range: the saved one is kept
    dialog.save()
    assert backend.settings.split_words == 50_000


def test_homes_tiles_start_at_the_top(flet_window: Window) -> None:
    """Convert's body is one line, Split's two: their icons and titles stay in line (024)."""
    app = flet_window(FakeBackend(settings=QUIET))
    for tile in app.home.tiles:
        style = tile.control.style
        assert style is not None and style.alignment == ft.Alignment.TOP_CENTER
        column = tile.control.content
        assert isinstance(column, ft.Column) and column.alignment == ft.MainAxisAlignment.START
    assert app.home.convert.control.style == app.home.split.control.style


def test_the_message_line_takes_room_only_with_a_message(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    assert not app.message.visible
    app.view.show_message("Something to say")
    assert app.message.visible and app.message.value == "Something to say"
    app.view.show_message("")
    assert not app.message.visible
