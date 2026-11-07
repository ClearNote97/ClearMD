"""Feature 018 — The actions: primary, Back, Cancel, Convert More, Enter and the F-1 pause (AC-04);
spec/features/018_*/spec.md. The flet window is built on a page that is not flet's (no screen).
"""

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import cast

import flet as ft
import pytest
from support.flet_acceptance import (
    QUIET,
    Held,
    Window,
    click,
    confirm,
    converted,
    page_of,
    pump,
    to_review,
    windows,
)
from support.gui_fakes import FakeBackend, planned

from clearmd.backend.schemas.models import BatchPlan
from clearmd.frontend.flet.views.dialogs.keep_inputs import KeepInputsDialog
from clearmd.frontend.flet.visuals.look import button_style
from clearmd.frontend.presenter import AppState


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def test_ac_04_next_next_convert_open_and_a_reason_when_disabled(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    labels = []
    for page in (1, 2, 3, 4):
        app.presenter.go_to(page)
        labels.append(app.actions.primary.content)
        assert app.actions.primary.disabled  # nothing chosen yet
        assert app.actions.hint.value  # and it says why
    assert labels == ["Next", "Next", "Convert", "Open Results Folder"]


def test_ac_04_back_goes_one_page_back_and_only_where_it_makes_sense(
    flet_window: Window, tmp_path: Path
) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    assert not app.actions.secondary.visible  # nothing to go back to on Choose
    to_review(app, tmp_path)
    assert app.actions.secondary.visible and app.actions.secondary.content == "Back"
    click(app.actions.secondary)
    assert app.presenter.page == 1 and not app.actions.secondary.visible


def test_ac_04_cancel_is_there_while_working_and_stops_at_once(
    flet_window: Window, tmp_path: Path
) -> None:
    held = Held()
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf")), (), ())
    fake = FakeBackend(plan=plan, settings=QUIET, before_finish=held)
    app = flet_window(fake)
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=held.started.is_set)
    pump(app, seconds=0.1)
    assert app.actions.secondary.visible and app.actions.secondary.content == "Cancel"
    click(app.actions.secondary)
    held.gate.set()
    pump(app, until=lambda: converted(app))
    assert app.presenter.state is AppState.CANCELLED and fake.run_calls[-1]["cancel"].is_set()


@pytest.mark.parametrize("keep", [True, False])
def test_ac_04_convert_more_asks_every_time(
    flet_window: Window, tmp_path: Path, keep: bool
) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    for _round in range(2):  # asked again the second time
        to_review(app, tmp_path)
        confirm(app)
        pump(app, until=lambda: app.presenter.page == 4)
        assert app.actions.strong  # prominent
        assert app.actions.secondary.style == button_style("strong")
        click(app.actions.secondary)
        dialog = app.dialogs.current
        assert isinstance(dialog, KeepInputsDialog) and page_of(app).dialogs == [dialog.control]
        refreshes = page_of(app).refreshes
        click(dialog.keep if keep else dialog.clear)
        assert app.dialogs.current is None and page_of(app).dialogs == []
        # Sent at once: closing the dialog had already updated flet's page, so without this the
        # Choose page showed only at the next click (the owner pressed twice, v1.0.1).
        assert page_of(app).refreshes > refreshes
        assert app.presenter.page == 1
        names = [row.name for row in app.main.inputs.rows()]
        assert names == ([f"{tmp_path.name}/"] if keep else [])
        if not keep:
            app.presenter.add_paths([tmp_path])


def test_ac_04_enter_runs_the_primary_action(flet_window: Window, tmp_path: Path) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    page = page_of(app)
    page.press("Enter")  # Home has no primary action (feature 023)
    assert app.presenter.page == 0
    app.presenter.go_to(1)
    page.press("Enter")  # nothing chosen: the action is disabled and does nothing
    assert app.presenter.page == 1 and app.presenter.state is AppState.READY
    app.presenter.add_paths([tmp_path])
    page.press("Enter")
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    assert app.presenter.page == 2
    page.press("Numpad Enter")  # the keypad's too
    assert app.presenter.page == 3


def focus(control: ft.BaseControl, *, gained: bool) -> None:
    """flet's program tells the window that ``control`` took (or lost) the keyboard focus."""
    cast(Callable[[], object], getattr(control, "on_focus" if gained else "on_blur"))()


def test_ac_04_enter_is_the_focused_controls_own(flet_window: Window, tmp_path: Path) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    page = page_of(app)
    app.presenter.add_paths([tmp_path])
    focus(app.main.clear, gained=True)
    page.press("Enter")  # Flutter presses the focused button: the window adds no Next to it
    assert app.presenter.page == 1 and app.presenter.state is AppState.READY
    focus(app.main.clear, gained=False)
    click(app.rail.help)
    assert app.dialogs.current is not None
    close = app.dialogs.current.foot.controls[-1]
    focus(close, gained=True)
    page.press("Enter")  # the same in a dialog: its focused button takes Enter
    assert app.dialogs.current is not None
    focus(close, gained=False)
    page.press("Enter")  # nothing focused: the dialog's default action
    assert app.dialogs.current is None
    page.press("Enter")  # and the window's again
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    assert app.presenter.page == 2


def test_ac_04_a_page_change_pauses_the_primary_action_f1(
    flet_window: Window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("clearmd.frontend.presenter.chrome.primary_gate.PRIMARY_PAUSE_SECONDS", 0.4)
    app = flet_window(FakeBackend(settings=QUIET))
    page = page_of(app)
    app.presenter.add_paths([tmp_path])
    pump(app, seconds=0.5)  # the pause of the first page is over
    page.press("Enter")
    pump(app, until=lambda: app.presenter.page == 2)
    assert app.actions.primary.disabled  # the pause is shown on the button
    page.press("Enter")  # a burst: the second press must not run Next past Review
    app.primary_button.press()
    assert app.presenter.page == 2
    pump(app, until=lambda: not app.actions.primary.disabled, seconds=2)
    assert not app.actions.primary.disabled
    page.press("Enter")
    assert app.presenter.page == 3


def test_ac_04_a_pause_cut_short_by_closing_never_ends(
    flet_window: Window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("clearmd.frontend.presenter.chrome.primary_gate.PRIMARY_PAUSE_SECONDS", 0.3)
    app = flet_window(FakeBackend(settings=QUIET))
    app.presenter.add_paths([tmp_path])
    pump(app, seconds=0.35)
    app.presenter.go_to(2)
    app.presenter.go_to(1)  # back on Choose: Next pauses
    assert app.actions.primary.disabled
    app.primary_button.cancel_pause()  # the window closing: the pause's end does nothing
    pump(app, seconds=0.4)
    assert app.actions.primary.disabled
