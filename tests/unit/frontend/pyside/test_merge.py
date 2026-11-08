"""Feature 026 in the Qt window: the Merge tile, How to Merge on step 1 in place of the images
(each choice sent to the presenter), and Merge's setting (AC-05)."""

from collections.abc import Callable
from dataclasses import replace

from PySide6.QtWidgets import QComboBox
from support.gui_fakes import FakeBackend
from support.pyside_acceptance import QUIET

from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.pyside import PySideApp
from clearmd.frontend.pyside.views.dialogs.settings import SettingsDialog

Window = Callable[..., PySideApp]


def test_the_third_tile_opens_step_1_of_merge_in_its_words(window: Window) -> None:
    app = window()
    tile = app.home.merge
    assert tile.title.text() == "Merge Documents" and tile.body.text()
    assert not tile.icon.pixmap().isNull()
    assert app.home.tiles == (app.home.convert.button, app.home.split.button, tile.button)
    widths = {button.width() for button in app.home.tiles}
    assert max(widths) - min(widths) <= 1  # one row, equal widths
    tile.button.click()
    assert app.presenter.page == 1 and app.presenter.tool is Tool.MERGE
    assert app.surface.title.text() != "Choose What to Convert"


def test_the_merge_block_shows_only_for_merge_and_sends_each_choice(window: Window) -> None:
    app = window()
    merge, split = app.main.merge, app.main.split
    app.presenter.choose_tool(Tool.MERGE)
    assert merge.widget.isVisible() and not split.widget.isVisible()
    assert not app.main.images_omit.isVisible() and app.main.summary_md.isVisible()
    assert merge.into["markdown"].isChecked()
    assert merge.into["pdf"].text() == "One PDF (PDF files only)"
    merge.into["pdf"].click()
    assert app.presenter.settings.merge_into == "pdf" and merge.into["pdf"].isChecked()
    merge.into["markdown"].click()
    assert app.presenter.settings.merge_into == "markdown"
    for tool, shown in ((Tool.SPLIT, split), (Tool.CONVERT, None)):
        app.presenter.choose_tool(tool)
        assert not merge.widget.isVisible()
        assert shown is None or shown.widget.isVisible()
    assert app.main.images_omit.isVisible()


def test_the_block_shows_the_remembered_choice(window: Window) -> None:
    app = window(FakeBackend(settings=replace(QUIET, merge_into="pdf")))
    app.presenter.choose_tool(Tool.MERGE)
    assert app.main.merge.into["pdf"].isChecked()


def test_the_settings_round_trip_merge_into(window: Window) -> None:
    backend = FakeBackend(settings=QUIET)
    app = window(backend)
    app.rail.settings.click()
    dialog = app.dialogs.current
    assert isinstance(dialog, SettingsDialog)
    combo = dialog.controls["merge_into"]
    assert isinstance(combo, QComboBox) and combo.currentText() == "One Markdown"
    combo.setCurrentText("One PDF (PDF files only)")
    dialog.save()
    assert backend.saved[-1].merge_into == "pdf" and app.presenter.settings.merge_into == "pdf"
    app.rail.settings.click()
    again = app.dialogs.current
    assert isinstance(again, SettingsDialog) and again.chosen().merge_into == "pdf"
    again.restore()
    assert again.chosen().merge_into == "markdown"
    again.close_dialog()
