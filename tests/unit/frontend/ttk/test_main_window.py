"""The ttk window's main screen on the presenter (005, T04), under a display."""

import time
import tkinter.font as tkfont
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from support.gui_fakes import FakeBackend

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter import AppState
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.layout import BODY, on_grid


@pytest.fixture
def app(display: str) -> Iterator[TtkApp]:
    window = TtkApp(FakeBackend(settings=Settings(show_welcome=False)))
    window.start()
    pump(window, seconds=0.2)
    yield window
    window.close()


def pump(window: TtkApp, *, until: Any = None, seconds: float = 2.0) -> None:
    """Run the UI loop for a moment (or until ``until()`` holds)."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        window.root.update()
        if until is not None and until():
            return
        time.sleep(0.01)


def widgets(root: Any) -> Iterator[Any]:
    pending = [root]
    while pending:
        widget = pending.pop()
        yield widget
        pending.extend(widget.winfo_children())


def test_the_window_shows_the_app_and_its_state(app: TtkApp) -> None:
    assert app.root.title() == "ClearMD"
    assert app.state_label.cget("text") == "Ready"
    assert str(app.main.convert.cget("state")) == "disabled"


def test_inputs_are_listed_and_enable_convert(app: TtkApp, tmp_path: Path) -> None:
    (tmp_path / "a.pdf").write_bytes(b"%PDF")
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path])
    pump(app, seconds=0.2)
    shown = [app.main.inputs.item(item, "text") for item in app.main.inputs.get_children()]
    assert shown == ["a.pdf", f"{tmp_path.name}/"]
    assert str(app.main.convert.cget("state")) == "normal"


def test_removing_the_selection_and_clearing(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path / "b.pdf"])
    first = app.main.inputs.get_children()[0]
    app.main.inputs.selection_set(first)
    app.main.remove.invoke()
    assert [app.main.inputs.item(i, "text") for i in app.main.inputs.get_children()] == ["b.pdf"]
    app.main.clear.invoke()
    assert app.main.inputs.get_children() == ()


def test_dropped_files_and_folders_are_added(app: TtkApp, tmp_path: Path) -> None:
    data = app.root.tk.call("list", str(tmp_path / "a b.pdf"), str(tmp_path))  # a space in a name
    app._dropped(SimpleNamespace(data=data))
    shown = [app.main.inputs.item(item, "text") for item in app.main.inputs.get_children()]
    assert shown[0] == "a b.pdf" and len(shown) == 2


def test_enter_triggers_convert_which_shows_the_plan(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path])
    app.root.event_generate("<Return>", when="tail")
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    assert app.presenter.state is AppState.WAITING_DECISION
    assert app.last_plan is not None


def test_both_themes_apply(app: TtkApp) -> None:
    app.apply_theme("dark")
    assert app.style.theme_use() == "bootstrap-dark"
    app.apply_theme("light")
    assert app.style.theme_use() == "bootstrap-light"


def test_the_language_changes_every_label(app: TtkApp) -> None:
    app.presenter.save_settings(Settings(language="es", show_welcome=False))
    pump(app, seconds=0.1)
    assert app.main.convert.cget("text") == "Convertir"
    assert app.main.add_folder.cget("text") == "Agregar carpeta"
    assert app.state_label.cget("text") == "Listo"


def test_every_gap_is_on_the_8_px_grid_and_text_is_at_least_14_px(app: TtkApp) -> None:
    off_grid = []
    for widget in widgets(app.root):
        manager = widget.winfo_manager()
        if manager not in {"pack", "grid"}:
            continue
        info = widget.pack_info() if manager == "pack" else widget.grid_info()
        for option in ("padx", "pady", "ipadx", "ipady"):
            value = info.get(option, 0)
            for part in value if isinstance(value, tuple) else str(value).split():
                if not on_grid(int(float(part))):
                    off_grid.append((str(widget), option, part))
    assert off_grid == []
    for name in ("TkDefaultFont", "TkTextFont", "TkHeadingFont"):
        assert tkfont.nametofont(name, root=app.root).cget("size") <= BODY  # pixels: negative
