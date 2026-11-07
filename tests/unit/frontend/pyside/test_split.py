"""Feature 023 in the Qt window: How to Split on step 1 in place of the images, each control sent to
the presenter (AC-09, AC-10), and the Split a PDF group of Settings."""

from collections.abc import Callable
from dataclasses import replace

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSpinBox
from support.gui_fakes import FakeBackend
from support.pyside_acceptance import QUIET, press, pump

from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.pyside import PySideApp
from clearmd.frontend.pyside.views.dialogs.settings import SettingsDialog

Window = Callable[..., PySideApp]


def images_shown(app: PySideApp) -> bool:
    return app.main.images_omit.isVisible() and app.main.images_folder.isVisible()


def test_the_split_block_is_shown_only_for_split_in_place_of_the_images(window: Window) -> None:
    app = window()
    app.presenter.choose_tool(Tool.CONVERT)
    assert not app.main.split.widget.isVisible() and images_shown(app)
    app.presenter.choose_tool(Tool.SPLIT)
    assert app.main.split.widget.isVisible() and not images_shown(app)
    assert app.main.summary_md.isVisible() and app.main.next_to.isVisible()  # they stay
    assert app.main.split.by_parts.text() == "Into" and app.main.split.parts.value() == 2
    assert app.main.split.pages.value() == 50 and app.main.split.keep["both"].isChecked()
    app.presenter.choose_tool(Tool.CONVERT)
    assert not app.main.split.widget.isVisible() and images_shown(app)


def test_each_split_control_is_sent_to_the_presenter(window: Window) -> None:
    app = window()
    app.presenter.choose_tool(Tool.SPLIT)
    split = app.main.split
    split.by_pages.click()
    assert app.presenter.settings.split_cut == "pages"
    split.by_parts.click()
    assert app.presenter.settings.split_cut == "parts"
    for value in ("pdf", "markdown", "both"):
        split.keep[value].click()
        assert app.presenter.settings.split_keep == value
    split.parts.setValue(4)
    split.pages.setValue(10)
    assert app.presenter.settings.split_parts == 4
    assert app.presenter.settings.split_pages == 10


def type_number(app: PySideApp, box: QSpinBox, text: str) -> None:
    box.setFocus()
    box.selectAll()
    pump(app, seconds=0.05)
    box.lineEdit().setText(text)  # typed: not sent yet (no keyboard tracking)


def test_a_typed_number_is_sent_on_enter_not_on_every_key(window: Window) -> None:
    app = window()
    app.presenter.choose_tool(Tool.SPLIT)
    box = app.main.split.parts
    type_number(app, box, "12")
    assert app.presenter.settings.split_parts == 2
    press(app, Qt.Key.Key_Return)
    assert app.presenter.settings.split_parts == 12
    assert app.presenter.page == 1  # Enter in the box is the number done, not Next


def test_the_boxes_show_what_the_presenter_keeps(window: Window) -> None:
    app = window(FakeBackend(settings=replace(QUIET, split_parts=7, split_pages=3)))
    app.presenter.choose_tool(Tool.SPLIT)
    assert app.main.split.parts.value() == 7 and app.main.split.pages.value() == 3
    app.presenter.choose_split(parts=1)  # out of range: refused, the box keeps 7
    assert app.main.split.parts.value() == 7


def test_the_settings_group_round_trips(window: Window) -> None:
    backend = FakeBackend(settings=replace(QUIET, split_cut="pages", split_keep="pdf"))
    app = window(backend)
    app.rail.settings.click()
    dialog = app.dialogs.current
    assert isinstance(dialog, SettingsDialog)
    group = dialog.split
    assert group.by_pages.isChecked() and group.keep.currentText() == "The parts as PDF"
    assert group.parts.value() == 2 and group.pages.value() == 50
    group.by_parts.setChecked(True)
    group.parts.setValue(5)
    group.pages.setValue(20)
    group.keep.setCurrentIndex(1)
    dialog.save()
    saved = backend.saved[-1]
    assert (saved.split_cut, saved.split_parts, saved.split_pages) == ("parts", 5, 20)
    assert saved.split_keep == "markdown"
    assert app.presenter.settings.split_parts == 5
    app.rail.settings.click()
    again = app.dialogs.current
    assert isinstance(again, SettingsDialog) and again.split.parts.value() == 5
    again.restore()
    assert again.chosen().split_parts == 2 and again.chosen().split_keep == "both"
    again.close_dialog()
