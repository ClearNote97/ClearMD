"""Keyboard and look (005, T07; AC-17 to AC-19, AC-22)."""

from pathlib import Path
from typing import Any

from support.ttk_unit import pump

from clearmd.frontend.presenter import Action, AppState
from clearmd.frontend.presenter.state import enabled_actions
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.views import dialogs

# --- Keyboard and look (T07; AC-17 – AC-19, AC-22) -----------------------------------------------


def focus_chain(app: TtkApp, start: Any, steps: int = 40) -> list[Any]:
    chain, widget = [], start
    for _ in range(steps):
        chain.append(widget)
        widget = widget.tk_focusNext()
        if widget is None or widget is start:
            break
    return chain


def test_tab_goes_through_the_first_step_in_reading_order(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path])
    pump(app, seconds=0.1)
    main = app.main
    chain = focus_chain(app, main.add_files)
    expected = [
        main.add_files, main.add_folder, main.inputs.tree, main.remove, main.clear,
        main.next_to, main.in_folder, main.pick, app.actions.primary,
    ]  # fmt: skip
    positions = [chain.index(widget) for widget in expected]
    assert positions == sorted(positions)
    assert app.rail.settings in chain and app.rail.help in chain  # the rail is reachable too


def test_enter_saves_the_settings_and_esc_cancels_them(app: TtkApp) -> None:
    app.rail.settings.invoke()
    pump(app, seconds=0.1)
    dialog = app.dialog
    assert isinstance(dialog, dialogs.settings.SettingsDialog)
    dialog.values["recursive"].set(False)
    dialog.focus_force()
    pump(app, seconds=0.1)
    dialog.event_generate("<Escape>", when="tail")
    pump(app, until=lambda: app.dialog is None, seconds=1.0)
    assert app.presenter.settings.recursive  # Esc: nothing saved
    app.rail.settings.invoke()
    pump(app, seconds=0.1)
    dialog = app.dialog
    assert isinstance(dialog, dialogs.settings.SettingsDialog)
    dialog.values["recursive"].set(False)
    dialog.focus_force()
    pump(app, seconds=0.1)
    dialog.event_generate("<Return>", when="tail")
    pump(app, until=lambda: app.dialog is None, seconds=1.0)
    assert not app.presenter.settings.recursive  # Enter: saved


def test_settings_and_help_are_never_disabled_together_with_help(app: TtkApp) -> None:
    for state in AppState:
        enabled = enabled_actions(state, has_inputs=True, can_confirm=True, has_results=True)
        assert Action.HELP in enabled  # "?" always works (UX §4)
