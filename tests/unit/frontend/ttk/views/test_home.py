"""Home, the start screen, and the rail's Home (feature 023, AC-08)."""

import threading
from pathlib import Path

from support.gui_close import shut
from support.gui_fakes import FakeBackend
from support.ttk_unit import pump, shown

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.state import HOME, Tool
from clearmd.frontend.ttk import TtkApp


def click_rail(app: TtkApp, step: int) -> None:
    x1, y1, x2, y2 = app.rail.bbox(f"step{step}")
    app.rail.event_generate("<Button-1>", x=(x1 + x2) // 2, y=(y1 + y2) // 2)
    pump(app, seconds=0.05)


def test_the_window_opens_on_home_with_its_two_tiles_and_no_action_bar(app: TtkApp) -> None:
    assert app.presenter.page == HOME and shown(app) is app.home
    header = app.surface.header()
    assert header == {
        "eyebrow": "",
        "title": "What Do You Want to Do?",
        "subtitle": "Everything happens on your computer: your documents never leave it.",
    }
    assert app.home.tiles[Tool.CONVERT].texts() == (
        "Convert to Markdown", "PDF, Word, Excel, PowerPoint, HTML and more",
    )  # fmt: skip
    assert app.home.tiles[Tool.SPLIT].texts()[0] == "Split a PDF"
    assert app.home.note.cget("text") == "The tools change files, never what is inside them."
    assert not app.actions.winfo_manager()  # no primary action on Home
    assert app.rail.home_text() == "> Home"
    assert app.rail.step_texts() == ["Choose", "Review", "Convert", "Results"]


def test_each_tile_opens_step_1_of_its_tool(app: TtkApp) -> None:
    app.home.tiles[Tool.SPLIT].event_generate("<Button-1>", x=10, y=10)
    pump(app, seconds=0.1)
    assert app.presenter.page == 1 and shown(app) is app.main
    assert app.surface.header()["title"] == "Choose What to Split"
    assert app.rail.step_texts()[2] == "Split"
    assert app.actions.winfo_manager() == "pack"  # the bar is back at the foot
    app.presenter.go_to(HOME)
    app.home.tiles[Tool.CONVERT].choose()
    pump(app, seconds=0.1)
    assert app.surface.header()["title"] == "Choose What to Convert"
    assert app.rail.step_texts() == ["> Choose", "Review", "Convert", "Results"]


def test_enter_and_space_on_a_focused_tile_choose_it(app: TtkApp) -> None:
    tile = app.home.tiles[Tool.SPLIT]
    app.root.deiconify()
    tile.focus_force()
    pump(app, until=lambda: app.root.focus_get() is tile, seconds=2)
    assert tile.cget("takefocus") and tile.lit  # drawn as chosen with the focus
    tile.event_generate("<Return>", when="tail")
    pump(app, until=lambda: app.presenter.page == 1)
    assert app.presenter.page == 1 and app.presenter.tool is Tool.SPLIT
    assert app.presenter.state is AppState.READY  # the window's Enter did not run too


def test_the_rail_s_home_and_ctrl_0_bring_it_back(app: TtkApp) -> None:
    app.presenter.choose_tool(Tool.CONVERT)
    click_rail(app, 0)
    assert app.presenter.page == HOME and shown(app) is app.home
    assert app.rail.home_text() == "> Home"
    app.presenter.go_to(1)
    app.root.event_generate("<Control-Key-0>")
    pump(app, seconds=0.05)
    assert app.presenter.page == HOME


def test_home_cannot_be_opened_while_the_work_runs(display: str, tmp_path: Path) -> None:
    gate = threading.Event()

    def held() -> None:  # the batch waits on its last file until the test lets it go
        gate.wait(5)

    window = TtkApp(FakeBackend(settings=Settings(show_welcome=False), before_finish=held))
    window.start()
    try:
        window.presenter.add_paths([tmp_path])  # dropped on Home: they go to step 1
        assert window.presenter.page == 1
        window.presenter.analyze()
        pump(window, until=lambda: window.presenter.state is AppState.WAITING_DECISION)
        window.presenter.confirm(overwrite=False)
        pump(window, until=lambda: window.presenter.state is AppState.CONVERTING)
        assert window.rail.home_text() == "- Home"
        click_rail(window, 0)
        assert window.presenter.page == 3
    finally:
        gate.set()
        pump(window, until=lambda: window.presenter.state is not AppState.CONVERTING)
        home = window.rail.home_text()
        shut(window)
    assert home == "Home"  # reachable again once the work ends
