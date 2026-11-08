"""Feature 033 on the ttk window (AC-04): "What Next?" as the three windows show it — the tools as
tiles in a row with the start screen's icons, the tool just used first with the accent, the box
under them, Cancel at the foot — and one click opening step 1 of a tool."""

from collections.abc import Callable
from pathlib import Path

from support.flet_acceptance import QUIET
from support.gui_fakes import FakeBackend
from support.ttk_unit import confirm, pump

from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.views.dialogs.what_next import ICON, WhatNextDialog
from clearmd.frontend.ttk.visuals import tool_marks


def test_ac_04_what_next_tiles_box_and_cancel(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    app = window(FakeBackend(settings=QUIET))
    app.home.tiles[Tool.SPLIT].choose()
    app.presenter.add_paths([tmp_path])
    app.presenter.analyze()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    confirm(app)
    pump(app, until=lambda: app.presenter.page == 4)
    app.actions.secondary.invoke()
    pump(app, seconds=0.2)
    dialog = app.dialog
    assert isinstance(dialog, WhatNextDialog)
    tiles = list(dialog.tiles.values())
    assert [tile.texts()[0] for tile in tiles] == ["Split Again", "Convert", "Merge"]
    assert [tile.current for tile in tiles] == [True, False, False]
    for tool, tile in dialog.tiles.items():  # the start screen's icons, smaller
        drawn, shared = tile.icon("#123456"), tool_marks.tool_icon(tool.value, "#123456", ICON)
        assert drawn.tobytes() == shared.tobytes()
    assert len({tile.winfo_rooty() for tile in tiles}) == 1  # in a row
    assert len({tile.winfo_width() for tile in tiles}) <= 2  # as wide (a pixel of rounding)
    box = dialog.keep_box
    assert box.winfo_rooty() > tiles[0].winfo_rooty() + tiles[0].winfo_height()  # under them
    assert bool(dialog.keep.get())
    assert dialog.cancel.winfo_rooty() > box.winfo_rooty()  # Cancel at the foot
    tiles[2].choose()  # Merge, the files kept
    pump(app, seconds=0.05)
    assert app.dialog is None and (app.presenter.page, app.presenter.tool) == (1, Tool.MERGE)
    assert app.main.inputs.names() == [f"{tmp_path.name}/"]
