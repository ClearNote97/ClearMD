"""Feature 016 — The actions: primary, Back, Cancel, Convert More, Enter and the F-1 pause (AC-04);
spec/features/016_*/spec.md. The PySide6 window runs offscreen, on the presenter's fake backend.
"""

from collections.abc import Callable
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut
from support.gui_fakes import FakeBackend, planned
from support.pyside_acceptance import (
    QUIET,
    Held,
    confirm,
    converted,
    press,
    pump,
    to_review,
)

from clearmd.backend.schemas.models import BatchPlan
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.state import HOME
from clearmd.frontend.pyside import PySideApp
from clearmd.frontend.pyside.views.dialogs.keep_inputs import KeepInputsDialog

Window = Callable[..., PySideApp]


def test_ac_04_next_next_convert_open_and_a_reason_when_disabled(qt_window: Window) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    labels = []
    for page in (1, 2, 3, 4):
        app.presenter.go_to(page)
        labels.append(app.actions.primary.text())
        assert not app.actions.primary.isEnabled()  # nothing chosen yet
        assert app.actions.hint.text()  # and it says why
    assert labels == ["Next", "Next", "Convert", "Open Results Folder"]


def test_ac_04_back_goes_one_page_back_and_only_where_it_makes_sense(
    qt_window: Window, tmp_path: Path
) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    assert not app.actions.secondary.isVisible()  # nothing to go back to on Choose
    to_review(app, tmp_path)
    assert app.actions.secondary.isVisible() and app.actions.secondary.text() == "Back"
    app.actions.secondary.click()
    assert app.presenter.page == 1


def test_ac_04_cancel_is_there_while_working_and_stops_at_once(
    qt_window: Window, tmp_path: Path
) -> None:
    held = Held()
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf")), (), ())
    fake = FakeBackend(plan=plan, settings=QUIET, before_finish=held)
    app = qt_window(fake)
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=held.started.is_set)
    pump(app, seconds=0.1)
    assert app.actions.secondary.isEnabled() and app.actions.secondary.text() == "Cancel"
    app.actions.secondary.click()
    held.gate.set()
    pump(app, until=lambda: converted(app))
    assert app.presenter.state is AppState.CANCELLED and fake.run_calls[-1]["cancel"].is_set()


@pytest.mark.parametrize("keep", [True, False])
def test_ac_04_convert_more_asks_every_time(qt_window: Window, tmp_path: Path, keep: bool) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    for _round in range(2):  # asked again the second time
        to_review(app, tmp_path)
        confirm(app)
        pump(app, until=lambda: app.presenter.page == 4)
        assert app.actions.secondary.objectName() == "strong"  # prominent
        app.actions.secondary.click()
        assert isinstance(app.dialogs.current, KeepInputsDialog)
        app.dialogs.current.answer("keep" if keep else "clear")  # What Next? since 032
        assert app.dialogs.current is None and app.presenter.page == 1
        names = [row.name for row in app.main.inputs.rows()]
        assert names == ([f"{tmp_path.name}/"] if keep else [])
        if not keep:
            app.presenter.add_paths([tmp_path])


def test_ac_04_enter_runs_the_primary_action(qt_window: Window, tmp_path: Path) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    press(app, Qt.Key.Key_Return)  # the start screen has no primary action (023, 032)
    assert app.presenter.page == HOME
    app.presenter.go_to(1)
    press(app, Qt.Key.Key_Return)  # nothing chosen: the action is disabled and does nothing
    assert app.presenter.page == 1 and app.presenter.state is AppState.READY
    app.presenter.add_paths([tmp_path])
    press(app, Qt.Key.Key_Return)
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    assert app.presenter.page == 2
    press(app, Qt.Key.Key_Enter)  # the keypad's too
    assert app.presenter.page == 3


def test_ac_04_a_held_enter_is_one_press(qt_window: Window) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    enters = [
        shortcut
        for shortcut in app.window.findChildren(QShortcut)
        if shortcut.key().toString() in {"Return", "Enter"}
    ]
    assert len(enters) == 2 and not any(shortcut.autoRepeat() for shortcut in enters)


def test_ac_04_a_page_change_pauses_the_primary_action_f1(
    qt_window: Window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("clearmd.frontend.presenter.chrome.primary_gate.PRIMARY_PAUSE_SECONDS", 0.4)
    app = qt_window(FakeBackend(settings=QUIET))
    app.presenter.add_paths([tmp_path])
    pump(app, seconds=0.5)  # the pause of the first page is over
    press(app, Qt.Key.Key_Return)
    pump(app, until=lambda: app.presenter.page == 2)
    assert not app.actions.primary.isEnabled()  # the pause is shown on the button
    press(app, Qt.Key.Key_Return)  # a burst: the second press must not run Next past Review
    app.actions.primary.click()
    assert app.presenter.page == 2
    pump(app, until=lambda: app.actions.primary.isEnabled(), seconds=2)
    assert app.actions.primary.isEnabled()
    press(app, Qt.Key.Key_Return)
    assert app.presenter.page == 3
