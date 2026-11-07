"""Feature 016 — The window, its steps and its look (AC-01, AC-06); spec/features/016_*/spec.md.

The PySide6 window runs offscreen, on the presenter's fake backend.
"""

import re
import tomllib
from collections.abc import Callable
from dataclasses import replace

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLayout, QPushButton, QStackedLayout, QWidget
from support.gui_fakes import FakeBackend
from support.pyside_acceptance import QUIET, ROOT, descendants, press, pump

import clearmd.frontend.presenter.presenter as presenter_module
from clearmd.frontend.design.metrics import GUTTER, on_grid
from clearmd.frontend.design.palette import DARK, LIGHT
from clearmd.frontend.design.typography import BODY
from clearmd.frontend.presenter.state import HOME, STEPS
from clearmd.frontend.pyside import PySideApp
from clearmd.frontend.pyside.visuals.stylesheet import stylesheet
from clearmd.i18n import load_catalog

Window = Callable[..., PySideApp]


def test_ac_01_clearmd_pyside_is_a_script_and_opens_the_window_on_the_presenter(
    qt_window: Window,
) -> None:
    scripts = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert scripts["project"]["gui-scripts"]["clearmd-pyside"] == "clearmd.frontend.pyside:main"
    app = qt_window(FakeBackend(settings=QUIET))
    assert app.window.isVisible() and not app.window.grab().isNull()
    assert not app.rail.mark.pixmap().isNull()  # the logo
    assert app.rail.wordmark.text().startswith("Clear")
    assert app.presenter.page == HOME and app.rail.home.property("current") == "true"  # 023
    assert app.rail.step_texts() == ["Choose", "Review", "Convert", "Results"]
    assert app.presenter.version in app.rail.foot.text()
    app.home.convert.button.click()
    assert app.rail.step_texts() == ["> Choose", "Review", "Convert", "Results"]
    assert app.presenter.page == 1


def test_ac_01_every_step_opens_by_click_and_by_ctrl_1_to_4(qt_window: Window) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    for step in (4, 2, 3, 1):
        app.rail.steps[step - 1].click()
        assert app.presenter.page == step
        assert app.view._stack.currentIndex() == step  # noqa: SLF001 -- 0 is the start screen
    for number, key in enumerate((Qt.Key.Key_3, Qt.Key.Key_4, Qt.Key.Key_2, Qt.Key.Key_1), 1):
        press(app, key, Qt.KeyboardModifier.ControlModifier)
        expected = {Qt.Key.Key_1: 1, Qt.Key.Key_2: 2, Qt.Key.Key_3: 3, Qt.Key.Key_4: 4}[key]
        assert app.presenter.page == expected, number
    assert app.rail.step_texts()[0] == "> Choose"
    assert len(app.rail.steps) == len(STEPS) == 4


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_01_the_texts_come_from_the_catalogs(qt_window: Window, language: str) -> None:
    app = qt_window(FakeBackend(settings=replace(QUIET, language=language)))
    catalog = load_catalog(language)
    assert app.window.windowTitle() == catalog.text("gui.app.title")
    assert app.surface.title.text() == catalog.text("gui.home.title")  # the start screen (023)
    app.presenter.go_to(1)
    assert app.surface.title.text() == catalog.text("gui.page.choose_title")
    assert app.surface.eyebrow.text()
    assert app.actions.primary.text() == catalog.text("gui.nav.next")
    assert app.main.add_files.text() == catalog.text("gui.main.add_files")
    assert app.rail.settings.text() == catalog.text("gui.main.settings")
    assert [text.removeprefix("> ") for text in app.rail.step_texts()] == [
        catalog.text(f"gui.steps.{name}") for name in STEPS
    ]


@pytest.mark.parametrize(("system", "palette"), [("dark", DARK), ("light", LIGHT)])
def test_ac_06_the_theme_follows_the_system_by_default(
    qt_window: Window, monkeypatch: pytest.MonkeyPatch, system: str, palette: object
) -> None:
    monkeypatch.setattr(presenter_module, "detect_system_theme", lambda: system)
    app = qt_window(FakeBackend(settings=QUIET))  # theme: "system"
    assert app.shown.palette is palette
    assert app.window.styleSheet() == stylesheet(app.shown.palette)


def test_ac_06_an_explicit_theme_wins_and_applies_at_once(qt_window: Window) -> None:
    app = qt_window(FakeBackend(settings=replace(QUIET, theme="dark")))
    assert app.shown.palette is DARK and DARK.rail in app.window.styleSheet()
    app.presenter.save_settings(replace(app.presenter.settings, theme="light"))
    assert app.shown.palette is LIGHT and LIGHT.ground in app.window.styleSheet()


def layouts_of(root: QWidget) -> list[QLayout]:
    found = [w.layout() for w in descendants(root)] + root.findChildren(QLayout)
    return [layout for layout in found if layout is not None]


def test_ac_06_the_8_px_grid_14_px_text_and_one_primary_action(qt_window: Window) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    for layout in layouts_of(app.window):
        margins = layout.contentsMargins()
        for value in (margins.left(), margins.top(), margins.right(), margins.bottom()):
            assert on_grid(value), (layout.parent(), value)
        if not isinstance(layout, QStackedLayout):  # a stack has one page: no gap to speak of
            assert on_grid(layout.spacing()), layout.parent()
    sizes = [int(size) for size in re.findall(r"font-size:\s*(\d+)px", stylesheet(LIGHT))]
    assert sizes and min(sizes) >= BODY and app.application.font().pixelSize() >= BODY
    for page in (1, 2, 3, 4):  # one primary action per screen: the bar's
        app.presenter.go_to(page)
        primaries = [
            w
            for w in descendants(app.window)
            if isinstance(w, QPushButton) and w.objectName() == "primary" and w.isVisible()
        ]
        assert primaries == [app.actions.primary]
    pump(app, seconds=0.05)


def test_ac_06_the_page_and_the_rail_share_one_gutter(qt_window: Window) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    pump(app, seconds=0.1)
    panel = app.window.findChild(QFrame, "panel")
    assert panel is not None
    top_left = panel.mapTo(app.window, panel.rect().topLeft())
    bottom = top_left.y() + panel.height()
    right = top_left.x() + panel.width()
    assert app.rail.geometry().top() == GUTTER and app.rail.geometry().bottom() + 1 == bottom
    assert app.window.height() - bottom == GUTTER and app.window.width() - right == GUTTER
    assert top_left.x() - app.rail.geometry().right() - 1 == GUTTER
