"""Feature 040 in the PySide6 window (audit v4): every row's whole "what to do", wrapped inside
the row (AC-05); colours that agree with the state (AC-10); a focus you can see on each control
type, apart from "last used" in What Next? (AC-11). Strings come from the catalog."""

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pytest
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QWidget
from support.gui_fakes import FakeBackend, planned
from support.pyside_acceptance import QUIET, confirm, converted, pump, to_review

from clearmd.backend.schemas.errors import ErrorCode, SkipReason
from clearmd.backend.schemas.models import (
    BatchPlan,
    BatchReport,
    ConversionOutcome,
    OutcomeStatus,
    SkippedItem,
)
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.models import Tone
from clearmd.frontend.presenter.screens.results import result_view
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.pyside import PySideApp
from clearmd.frontend.pyside.views.dialogs.what_next import WhatNextDialog
from clearmd.i18n import load_catalog

Window = Callable[..., PySideApp]


def test_ac_05_the_whole_what_to_do_is_in_the_row(qt_window: Window) -> None:
    app = qt_window(FakeBackend(settings=replace(QUIET, language="es")))
    app.window.resize(800, 600)
    catalog = load_catalog("es")
    crashed = ConversionOutcome(
        planned("informe.pdf"), OutcomeStatus.FAILED, ErrorCode.WORKER_CRASHED
    )
    now = datetime.now()
    report = BatchReport(now, now, (crashed,), (), (), False)
    view = result_view(catalog, report, AppState.FINISHED_WITH_PROBLEMS)
    detail = view.rows[0].detail
    assert len(detail.split()) > 40  # the catalog's longest message, with its report
    app.view.show_result(view)
    app.presenter.go_to(4)
    pump(app, seconds=0.2)
    tree = app.results.problems.tree
    item = tree.topLevelItem(0)
    assert item is not None and item.text(2) == detail  # the whole text, in the row
    assert tree.wordWrap() and tree.textElideMode() is Qt.TextElideMode.ElideNone  # never "…"
    width = tree.header().sectionSize(2)
    lines = tree.fontMetrics().boundingRect(
        QRect(0, 0, width - 8, 100_000), Qt.TextFlag.TextWordWrap, detail
    )
    assert lines.height() > 2 * tree.fontMetrics().lineSpacing()  # it takes several lines
    assert tree.visualItemRect(item).height() >= lines.height()  # and the row holds them all
    assert app.results.problems.selected_indexes() == []  # still no row chosen for the user


def test_ac_10_the_colours_agree_with_the_state(qt_window: Window, tmp_path: Path) -> None:
    only_markdown = SkippedItem(Path("/docs/notes.md"), SkipReason.ALREADY_MARKDOWN)
    plan = BatchPlan((planned("a.pdf"), planned("bad.pdf")), (only_markdown,), ())
    backend = FakeBackend(settings=QUIET, plan=plan, statuses={"bad.pdf": OutcomeStatus.FAILED})
    app = qt_window(backend)
    app.presenter.choose_tool(Tool.CONVERT)
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=lambda: converted(app) and app.presenter.page == 4, seconds=10)
    assert app.presenter.state is AppState.FINISHED_WITH_PROBLEMS
    assert app.surface.eyebrow.property("tone") == "warning"  # the state's colour
    result = app.shown.last_result
    assert result is not None
    shown = app.results.stats.tones()
    assert shown == [stat.tone.value for stat in result.stats]  # each figure as sent
    skipped = catalog_stat(result.stats, load_catalog("en").text("gui.result.stat_skipped"))
    assert skipped is None or skipped is not Tone.WARNING  # a .md asks for nothing


def catalog_stat(stats: tuple[object, ...], label: str) -> Tone | None:
    for stat in stats:
        if getattr(stat, "label", "").startswith(label.split()[0]):
            return getattr(stat, "tone", None)
    return None


def grab(widget: QWidget) -> QImage:
    pump_events()
    return widget.grab().toImage()


def pump_events() -> None:
    application = QApplication.instance()
    if application is not None:
        application.processEvents()


def with_and_without_focus(widget: QWidget, other: QWidget) -> tuple[QImage, QImage]:
    window = widget.window()
    window.activateWindow()
    pump_events()
    other.setFocus()
    plain = grab(widget)
    widget.setFocus()
    assert widget.hasFocus()
    return grab(widget), plain


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_ac_11_every_control_type_shows_its_focus(
    qt_window: Window, tmp_path: Path, theme: str
) -> None:
    app = qt_window(FakeBackend(settings=replace(QUIET, theme=theme)))
    app.window.activateWindow()
    app.presenter.choose_tool(Tool.CONVERT)
    app.presenter.add_paths([tmp_path])
    pump(app, seconds=0.8)
    main = app.main
    controls = (main.inputs.tree, main.deselect, main.add_files)  # a list, a link, a button
    for control in controls:
        focused, plain = with_and_without_focus(control, main.summary_md)
        assert focused != plain, control.objectName() or type(control).__name__
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=lambda: converted(app) and app.presenter.page == 4, seconds=10)
    secondary = app.actions.secondary  # "What Next?"
    focused, plain = with_and_without_focus(secondary, app.actions.primary)
    assert focused != plain
    secondary.setObjectName("strong")  # the prominent look has its own focus too
    app.actions.show_secondary(secondary.text(), app.dialogs.what_next, strong=True)
    focused, plain = with_and_without_focus(secondary, app.actions.primary)
    assert focused != plain
    app.presenter.go_to(0)  # the start screen's tiles
    pump(app, seconds=0.1)
    tile = app.home.split.button
    focused, plain = with_and_without_focus(tile, app.home.convert.button)
    assert focused != plain


def test_ac_11_what_next_tells_focus_from_last_used(qt_window: Window, tmp_path: Path) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    app.presenter.choose_tool(Tool.CONVERT)
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=lambda: converted(app) and app.presenter.page == 4, seconds=10)
    app.actions.secondary.click()
    dialog = app.dialogs.current
    assert isinstance(dialog, WhatNextDialog)
    dialog.activateWindow()
    last_used, other = dialog.tiles[0].button, dialog.tiles[1].button
    assert last_used.property("current") == "true"
    dialog.keep.setFocus()
    plain_last = grab(last_used)
    other.setFocus()
    focused_other = grab(other)
    other_plain = grab(dialog.tiles[2].button)
    assert focused_other != other_plain  # the focus shows
    border = (1, focused_other.height() // 2)  # the left border, half-way down
    assert focused_other.pixel(*border) != plain_last.pixel(*border)  # not the last used's look
    dialog.close_dialog()
