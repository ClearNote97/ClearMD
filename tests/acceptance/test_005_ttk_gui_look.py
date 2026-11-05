"""Feature 005 — Look and keyboard (AC-16 to AC-19); spec/features/005_*/spec.md.

The window runs under a display (a virtual one when there is none), mostly on a fake backend.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from support.gui_fakes import FakeBackend
from support.ttk_acceptance import QUIET, press_enter, pump, widgets

import clearmd.frontend.presenter.presenter as presenter_module
from clearmd.frontend.design.metrics import on_grid
from clearmd.frontend.presenter import AppState
from clearmd.frontend.ttk import TtkApp, layout
from clearmd.frontend.ttk.visuals.style_names import PRIMARY


@pytest.mark.parametrize(
    ("system", "theme"), [("dark", "clearmd-dark"), ("light", "clearmd-light")]
)
def test_ac_16_the_theme_follows_the_system_by_default(
    window: Callable[..., TtkApp], monkeypatch: pytest.MonkeyPatch, system: str, theme: str
) -> None:
    monkeypatch.setattr(presenter_module, "detect_system_theme", lambda: system)
    app = window(FakeBackend(settings=QUIET))  # theme: "system"
    assert app.style.theme_use() == theme


def test_ac_17_the_8_px_grid_14_px_text_and_one_primary_action_per_screen(
    window: Callable[..., TtkApp],
) -> None:
    app = window(FakeBackend(settings=QUIET))
    for widget in widgets(app.root):
        manager = widget.winfo_manager()
        if manager not in {"pack", "grid"}:
            continue
        info = widget.pack_info() if manager == "pack" else widget.grid_info()
        for option in ("padx", "pady", "ipadx", "ipady"):
            value = info.get(option, 0)
            for part in value if isinstance(value, tuple) else str(value).split():
                assert on_grid(int(float(part))), (str(widget), option, part)
    assert all(font.cget("size") <= layout.units.BODY for font in app.fonts.values())  # px: < 0
    # One primary action per screen: the page's bar holds the only one (ADR-0029).
    primaries = [w for w in widgets(app.surface.page) if styled(w) == PRIMARY]
    assert primaries == [app.actions.primary]


def styled(widget: Any) -> str:
    try:
        return str(widget.cget("style"))
    except Exception:  # noqa: BLE001 -- a classic Tk widget has no style
        return ""


def test_ac_18_everything_works_with_the_keyboard(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    app = window(FakeBackend(settings=QUIET))
    app.presenter.add_paths([tmp_path])
    pump(app, seconds=0.1)
    chain: list[Any] = []
    widget: Any = app.main.add_files
    for _ in range(40):
        chain.append(widget)
        widget = widget.tk_focusNext()
        if widget is None or widget is app.main.add_files:
            break
    assert {app.main.add_folder, app.main.inputs.tree, app.actions.primary} <= set(chain)
    press_enter(app)  # Enter: the primary action
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    app.rail.help.invoke()
    assert app.dialog is not None
    app.dialog.focus_force()
    pump(app, seconds=0.1)
    app.dialog.event_generate("<Escape>", when="tail")  # Esc closes a dialog
    pump(app, until=lambda: app.dialog is None, seconds=1.0)
    assert app.dialog is None


def test_ac_19_nothing_is_reachable_only_by_hover(window: Callable[..., TtkApp]) -> None:
    app = window(FakeBackend(settings=QUIET))
    hovering = [
        str(widget) for widget in widgets(app.root) if "<Enter>" in widget.bind()
    ]  # no tooltip, no hover-only control
    assert hovering == []
