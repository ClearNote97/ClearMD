"""Results' "What Next?" (feature 033): the three tools as tiles, the one just used first, one box
for the files, Cancel."""

from pathlib import Path

from support.gui_close import shut
from support.gui_fakes import FakeBackend, planned
from support.ttk_unit import confirm, pump

from clearmd.backend.schemas.models import BatchPlan
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.views.dialogs.what_next import WhatNextDialog


def open_it(
    app: TtkApp, tmp_path: Path, tool: Tool = Tool.CONVERT, paths: list[Path] | None = None
) -> WhatNextDialog:
    app.presenter.choose_tool(tool)
    app.presenter.add_paths(paths or [tmp_path])
    app.presenter.analyze()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    confirm(app)
    pump(app, until=lambda: app.presenter.page == 4)
    assert app.actions.secondary.cget("text") == "What Next?"
    app.actions.secondary.invoke()
    pump(app, seconds=0.1)
    dialog = app.dialog
    assert isinstance(dialog, WhatNextDialog)
    return dialog


def test_the_tiles_the_box_and_cancel(app: TtkApp, tmp_path: Path) -> None:
    dialog = open_it(app, tmp_path)
    assert dialog.title() == "What Next?"
    assert [tile.texts()[0] for tile in dialog.tiles.values()] == [
        "Convert Again",
        "Split",
        "Merge",
    ]
    assert [tile.current for tile in dialog.tiles.values()] == [True, False, False]
    tops = {tile.winfo_rooty() for tile in dialog.tiles.values()}
    assert len(tops) == 1  # one row
    assert bool(dialog.keep.get()) and dialog.keep_box.cget("text") == "Keep the files you chose"
    assert dialog.cancel.cget("text") == "Cancel"
    dialog.cancel.invoke()
    pump(app, seconds=0.05)
    assert app.dialog is None and app.presenter.page == 4  # Results stays


def test_the_tool_just_used_comes_first(display: str, tmp_path: Path) -> None:
    files = [tmp_path / f"{name}.md" for name in ("a", "b")]  # Merge needs two documents (035)
    for file in files:
        file.write_text(file.stem, "utf-8")
    plan = BatchPlan((planned("a.md"), planned("b.md")), (), ())
    app = TtkApp(FakeBackend(plan=plan, settings=Settings(show_welcome=False, theme="light")))
    try:
        app.start()
        dialog = open_it(app, tmp_path, Tool.MERGE, files)
        assert list(dialog.tiles) == [Tool.MERGE, Tool.CONVERT, Tool.SPLIT]
        assert next(iter(dialog.tiles.values())).texts()[0] == "Merge Again"
    finally:
        shut(app)


def test_a_tile_opens_its_tool_with_the_files(app: TtkApp, tmp_path: Path) -> None:
    dialog = open_it(app, tmp_path)
    dialog.tiles[Tool.SPLIT].event_generate("<Button-1>", x=8, y=8)
    pump(app, seconds=0.1)
    assert app.dialog is None
    assert (app.presenter.page, app.presenter.tool) == (1, Tool.SPLIT)
    assert app.main.inputs.names() == [f"{tmp_path.name}/"]


def test_unticked_it_starts_empty_and_ticked_again_next_time(app: TtkApp, tmp_path: Path) -> None:
    dialog = open_it(app, tmp_path)
    dialog.keep_box.invoke()  # untick
    assert not dialog.keep.get()
    dialog.tiles[Tool.CONVERT].choose()
    pump(app, seconds=0.05)
    assert (app.presenter.page, app.main.inputs.names()) == (1, [])
    again = open_it(app, tmp_path)
    assert bool(again.keep.get())  # ticked every time it opens
    again.event_generate("<Escape>")  # Escape: only closes
    pump(app, until=lambda: app.dialog is None, seconds=1)
    assert app.presenter.page == 4
