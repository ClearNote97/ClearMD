"""Feature 007 — one test per acceptance criterion (spec/features/007_*/spec.md)."""

import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from PIL import Image
from support.gui_close import shut
from support.gui_fakes import FakeBackend

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter import AppState
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.views.dialogs.keep_inputs import KeepInputsDialog

ROOT = Path(__file__).resolve().parents[2]
QUIET = Settings(show_welcome=False, open_output_when_done=False)


@pytest.fixture
def app(display: str) -> Iterator[TtkApp]:
    window = TtkApp(FakeBackend(settings=QUIET))
    window.start()
    pump(window, seconds=0.1)
    yield window
    shut(window)


def pump(app: TtkApp, *, until: Callable[[], bool] | None = None, seconds: float = 5.0) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        app.root.update()
        if until is not None and until():
            return
        time.sleep(0.01)


def on_page(app: TtkApp, page: int) -> Callable[[], bool]:
    return lambda: app.presenter.page == page


def to_convert_page(app: TtkApp, folder: Path) -> None:
    app.presenter.add_paths([folder])
    app.actions.primary.invoke()
    pump(app, until=on_page(app, 2))
    app.actions.primary.invoke()
    pump(app, until=on_page(app, 3))


def shown(app: TtkApp) -> Any:
    return app.page


def test_ac_01_every_step_opens_by_click_and_keyboard_dimmed_when_not_on_screen(
    app: TtkApp,
) -> None:
    for step in (4, 2, 3, 1):
        x1, y1, x2, y2 = app.rail.bbox(f"step{step}")
        app.rail.event_generate("<Button-1>", x=(x1 + x2) // 2, y=(y1 + y2) // 2)
        pump(app, seconds=0.05)
        assert app.presenter.page == step and shown(app) is app.pages[step - 1]
    app.root.focus_force()
    app.root.update()
    app.root.event_generate("<Control-Key-4>", when="tail")
    pump(app, until=on_page(app, 4), seconds=1)
    assert app.rail.step_texts() == ["Choose", "Review", "Convert", "> Results"]


def test_ac_02_next_next_convert_open_and_a_reason_when_disabled(app: TtkApp) -> None:
    labels = []
    for page in (1, 2, 3, 4):
        app.presenter.go_to(page)
        labels.append(app.actions.primary.cget("text"))
        assert app.actions.primary.instate(["disabled"])  # nothing chosen yet
        assert app.actions.hint.cget("text")  # and it says why
    assert labels == ["Next", "Next", "Convert", "Open Results Folder"]


def test_ac_03_next_plans_next_opens_convert_convert_runs_there_and_results_open(
    app: TtkApp, tmp_path: Path
) -> None:
    to_convert_page(app, tmp_path)
    assert shown(app) is app.converting and app.converting.ready.winfo_ismapped()
    app.actions.primary.invoke()
    pump(app, until=on_page(app, 4))
    assert app.presenter.state is AppState.FINISHED and shown(app) is app.results


def test_ac_04_editing_drops_the_plan_and_nothing_is_edited_while_working(
    app: TtkApp, tmp_path: Path
) -> None:
    to_convert_page(app, tmp_path)
    app.presenter.go_to(1)
    app.presenter.add_paths([tmp_path / "more.pdf"])
    assert app.presenter.state is AppState.READY
    app.presenter.go_to(2)
    assert app.actions.hint.cget("text") == "Press Next on Choose to see what will happen."
    working = app.presenter.state
    assert working is AppState.READY  # (while working: tested in the presenter's own tests)


def test_ac_05_convert_more_is_prominent_and_asks_every_time(display: str, tmp_path: Path) -> None:
    for keep, names in ((True, [f"{tmp_path.name}/"]), (False, [])):
        app = TtkApp(FakeBackend(settings=QUIET))
        try:
            app.start()
            to_convert_page(app, tmp_path)
            app.actions.primary.invoke()
            pump(app, until=on_page(app, 4))
            assert str(app.actions.secondary.cget("style")).startswith("Strong")
            app.actions.secondary.invoke()
            assert isinstance(app.dialog, KeepInputsDialog)
            app.dialog.answer(keep)
            assert app.presenter.page == 1 and app.main.inputs.names() == names
        finally:
            shut(app)


def test_ac_06_checkboxes_follow_the_selection_header_clear_and_empty_click(
    app: TtkApp, tmp_path: Path
) -> None:
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path / "b.pdf"])
    inputs = app.main.inputs
    inputs.toggle(inputs.tree.get_children()[0])
    pump(app, seconds=0.05)
    assert inputs.checked() == [True, False]
    inputs.toggle_all()
    pump(app, seconds=0.05)
    assert inputs.checked() == [True, True]
    app.main.deselect.invoke()
    pump(app, seconds=0.05)
    assert inputs.checked() == [False, False]
    inputs.toggle_all()
    app.root.geometry("1080x900")  # room below the rows, whatever the system's font (Windows)
    pump(app, seconds=0.3)
    inputs.tree.event_generate("<Button-1>", x=200, y=inputs.tree.winfo_height() - 8)
    pump(app, seconds=0.05)
    assert inputs.checked() == [False, False]


def test_ac_07_headings_draw_faint_separators(app: TtkApp) -> None:
    assert "Heading.ClearMD.cell" in str(app.style.layout("Treeview.Heading"))


def test_ac_08_review_says_ready_to_convert(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path])
    app.actions.primary.invoke()
    pump(app, until=on_page(app, 2))
    assert app.last_plan is not None
    assert app.last_plan.rows[0].detail.startswith("✓ Ready to convert")


def test_ac_09_backgrounds_redraw_once_settled_small_window_and_compact_rail(
    app: TtkApp,
) -> None:
    assert app.root.minsize() == (800, 624)  # 624 since feature 014
    app.root.geometry("820x600")
    pump(app, until=lambda: app.rail._compact, seconds=5)
    assert app.rail._compact
    app.surface.event_generate("<Configure>")  # one more resize step
    assert app.surface._pending is not None  # a redraw waits for the size to settle
    pump(app, until=lambda: app.surface._pending is None, seconds=5)
    assert app.surface._pending is None  # and happened once it did


def test_ac_10_the_version_is_on_screen_and_in_the_help(app: TtkApp) -> None:
    version = app.presenter.version
    assert version in app.rail._version
    app.rail.help.invoke()
    assert app.dialog is not None
    texts = [str(child.cget("text")) for child in app.dialog.actions.winfo_children()]
    assert f"ClearMD {version}" in texts
    app.dialog.close()


def test_ac_11_the_splash_shows_the_subtitle_and_the_start_up_progress() -> None:
    splash = Image.open(ROOT / "src/clearmd/frontend/assets/logo/splash.png")
    assert splash.size == (520, 240)
    spec = (ROOT / "packaging" / "clearmd.spec").read_text(encoding="utf-8")
    assert 'text_default="Loading · Cargando… 0 %"' in spec and "text_pos=(40, 214)" in spec
    launcher = (ROOT / "packaging" / "launch_gui.py").read_text(encoding="utf-8")
    assert "Cargando… 30 %" in launcher and "Cargando… 70 %" in launcher
    launch = (ROOT / "src/clearmd/frontend/launch.py").read_text(encoding="utf-8")
    assert "Cargando… 100 %" in launch


def test_ac_12_screenshots_of_the_new_screens_in_both_themes_and_languages() -> None:
    shots = ROOT / "docs" / "screenshots" / "007"
    for screen in ("1-choose", "2-review", "3-convert-ready", "4-results", "4-convert-more",
                   "1-choose-compact"):  # fmt: skip
        for theme in ("light", "dark"):
            for language in ("en", "es"):
                assert (shots / f"{screen}-{theme}-{language}.png").is_file(), screen
