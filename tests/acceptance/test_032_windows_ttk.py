"""Feature 032 on the ttk window (AC-04, AC-05): the start screen's tiles centred with the icons
of ``design.tool_art``; Merge's order buttons, "What Next?" with Go Back Home, and no button that
looks pressed or focused when a page opens."""

from collections.abc import Callable
from pathlib import Path

from support.flet_acceptance import QUIET
from support.gui_fakes import FakeBackend
from support.ttk_unit import confirm, pump

from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.state import HOME, Tool
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.views.dialogs.keep_inputs import KeepInputsDialog
from clearmd.frontend.ttk.visuals import tool_marks


def test_ac_04_the_tiles_are_centred_with_the_app_s_own_icons(
    window: Callable[..., TtkApp],
) -> None:
    app = window(FakeBackend(settings=QUIET))
    pump(app, seconds=0.3)
    tiles = app.home.tiles
    for tool, tile in tiles.items():  # drawn from tool_art's shapes, as Qt and flet do
        drawn, shared = tile.icon("#123456"), tool_marks.tool_icon(tool.value, "#123456")
        assert drawn.tobytes() == shared.tobytes(), tool
    card = next(iter(tiles.values())).master
    left = min(tile.winfo_rootx() for tile in tiles.values()) - card.winfo_rootx()
    right = card.winfo_rootx() + card.winfo_width()
    right -= max(tile.winfo_rootx() + tile.winfo_width() for tile in tiles.values())
    assert abs(left - right) <= 1  # centred across the page
    note = app.home.note
    top = next(iter(tiles.values())).winfo_rooty() - card.winfo_rooty()
    bottom = card.winfo_rooty() + card.winfo_height() - (note.winfo_rooty() + note.winfo_height())
    assert abs(top - bottom) <= 2  # and down it: the tiles and the note in the middle


def test_ac_05_order_buttons_what_next_home_and_a_calm_focus(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    app = window(FakeBackend(settings=QUIET))
    files = [tmp_path / f"{name}.md" for name in ("a", "b")]
    for file in files:
        file.write_text(file.stem, "utf-8")
    app.home.tiles[Tool.MERGE].choose()
    app.presenter.add_paths(files)
    pump(app, seconds=0.1)
    tree = app.main.inputs.tree
    tree.selection_set(tree.get_children()[1])
    pump(app, seconds=0.05)
    assert app.main.move_up.winfo_ismapped() and app.main.move_up.instate(["!disabled"])
    app.main.move_up.invoke()
    pump(app, seconds=0.05)
    assert app.main.inputs.names() == ["b.md", "a.md"]
    primary = app.actions.primary
    app.root.deiconify()
    primary.focus_force()
    pump(app, until=lambda: app.root.focus_get() is primary, seconds=2)
    primary.invoke()  # Next: Review opens; the button does not keep the focus ring
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    pump(app, seconds=0.1)
    assert not primary.instate(["focus"])
    confirm(app)
    pump(app, until=lambda: app.presenter.page == 4)
    assert app.actions.secondary.cget("text") == "What Next?"
    app.actions.secondary.invoke()
    dialog = app.dialog
    assert isinstance(dialog, KeepInputsDialog) and dialog.home.cget("text") == "Go Back Home"
    dialog.home.invoke()
    pump(app, seconds=0.05)
    assert app.presenter.page == HOME and app.main.inputs.names() == ["b.md", "a.md"]
