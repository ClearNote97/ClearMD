"""Held keys and bursts (feature 007, F-1, A7-*)."""

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import pytest
from support.ttk_unit import confirm, pump, what_next

from clearmd.frontend.presenter import AppState
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.window import primary_button

# --- Adversarial check of 007 (F-1, A7-*) --------------------------------------------------------


def key(name: str, time_ms: int) -> SimpleNamespace:
    return SimpleNamespace(keysym=name, time=time_ms)


def test_a_held_key_is_one_press_on_windows_and_on_x11() -> None:
    from clearmd.frontend.ttk.window.presses import Presses

    windows = Presses()  # Windows repeats the press
    assert [windows.pressed(key("Return", t)) for t in (0, 500, 530)] == [True, False, False]
    windows.released(key("Return", 600))
    assert windows.pressed(key("Return", 900))
    x11 = Presses()  # X11 repeats a release and a press with the same time
    assert x11.pressed(key("Return", 0))
    x11.released(key("Return", 500))
    assert not x11.pressed(key("Return", 500))
    x11.released(key("Return", 700))
    assert x11.pressed(key("Return", 950))


def test_f1_a_held_enter_runs_one_action_whatever_the_pages(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path])
    for time_ms in range(0, 3000, 30):  # three seconds of a held Enter
        app.inputs.enter(key("Return", time_ms + 1))  # Windows: presses only, no release
        pump(app, seconds=0.01)
    pump(app, until=lambda: app.presenter.page == 2)
    assert app.presenter.page == 2 and app.presenter.state is AppState.WAITING_DECISION


def test_f1_the_pause_after_a_page_change_is_shown_on_the_button(
    app: TtkApp, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Deterministic (Windows CI, 040): the gate reads a clock the test moves, and the pause's end
    is the very callback the window schedules, run when the test says, not when a runner gets
    to it. What it checks is unchanged: disabled right after the page change, through the
    analysis's end, enabled when the pause is over."""
    clock = [100.0]
    monkeypatch.setattr(primary_button, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    monkeypatch.setattr("clearmd.frontend.presenter.chrome.primary_gate.PRIMARY_PAUSE_SECONDS", 0.3)
    ends: list[tuple[int, Callable[[], None]]] = []
    real_after = app.root.after

    def after(ms: int, callback: Callable[[], None]) -> str:
        if getattr(callback, "__name__", "") == "_end_pause":
            ends.append((ms, callback))
            return "held"
        return str(real_after(ms, callback))

    monkeypatch.setattr(app.root, "after", after)
    monkeypatch.setattr(app.root, "after_cancel", lambda _id: None)
    app.presenter.go_to(1)  # the window opens on Home (feature 023); step 1's pause starts
    app.presenter.add_paths([tmp_path])
    clock[0] += 1.0  # step 1's pause is over: the press counts
    app.primary_button.press()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    assert app.presenter.page == 2
    assert ends and ends[-1][0] == 300  # step 2's pause, as long as the gate says
    assert app.actions.primary.instate(["disabled"])  # shown, even after the analysis ended
    ends[-1][1]()  # the pause is over
    assert app.actions.primary.instate(["!disabled"])


def test_f1_a_state_shown_during_the_pause_keeps_the_button_disabled(
    app: TtkApp, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A quick analysis ends inside the pause (Windows CI, 040): showing its state, which enables
    the primary, must not end the pause early."""
    monkeypatch.setattr("clearmd.frontend.presenter.chrome.primary_gate.PRIMARY_PAUSE_SECONDS", 5.0)
    app.presenter.add_paths([tmp_path])  # step 1, Next enabled
    app.presenter.go_to(2)
    app.presenter.go_to(1)  # a page change: the pause starts
    assert app.state is not None and app.state.primary.enabled
    assert app.actions.primary.instate(["disabled"])
    app.view.show_state(app.state)  # the same page again, as a quick state shows it
    assert app.actions.primary.instate(["disabled"])  # still paused


def test_a7_1_convert_more_leaves_nothing_of_the_last_batch(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path])
    app.primary_button.press()
    pump(app, until=lambda: app.presenter.page == 2)
    confirm(app)
    pump(app, until=lambda: app.presenter.page == 4)
    what_next(app, keep=True)
    assert app.review.files.names() == [] and app.results.stats.dimmed  # waiting, faded (014)
    assert {value for _, value in app.results.stats.figures()} == {"—"}
    assert not app.converting.progress_card.winfo_ismapped()


def test_a7_2_the_secondary_button_keeps_one_command(app: TtkApp) -> None:
    first = app.actions.secondary.cget("command")
    for page in (2, 3, 2, 3):
        app.presenter.go_to(page)
    assert app.actions.secondary.cget("command") == first


def test_a7_3_a_burst_of_resizes_leaves_one_redraw_waiting(app: TtkApp) -> None:
    for _ in range(5):
        app.surface.event_generate("<Configure>")
        app.rail.redraw_soon()
        app.rail.set_compact(not app.rail._compact)
    waiting = [app.root.tk.call("after", "info", t) for t in app.root.tk.call("after", "info")]
    # One redraw at most per widget that draws: surface, rail, drop zone, and Home's tiles (023),
    # whose own first-size redraw may still be waiting when the test starts.
    assert sum("_redraw_now" in str(script) for script in waiting) <= 3 + len(app.home.tiles)


def test_c7_7_arrows_move_the_focus_so_checks_add_up(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path / f"{n}.pdf" for n in range(4)])
    inputs = app.main.inputs
    tree = inputs.tree
    tree.focus(tree.get_children()[0])
    inputs.shortcuts.toggle_focused()
    inputs.shortcuts.move(1, False)
    inputs.shortcuts.move(1, False)
    inputs.shortcuts.toggle_focused()
    pump(app, seconds=0.05)
    assert inputs.checked() == [True, False, True, False]
    inputs.shortcuts.move(1, True)
    pump(app, seconds=0.05)
    assert inputs.checked() == [True, False, True, True]
