"""Merge's order, "What Next?" and the calm focus of a page that opens (feature 032, AC-05), and
step 1 of Split at the smallest window (the list keeps its rows)."""

from dataclasses import replace
from pathlib import Path

from support.ttk_unit import confirm, pump

from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.state import HOME, Tool
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.views.dialogs.keep_inputs import KeepInputsDialog


def merge_three(app: TtkApp, tmp_path: Path) -> list[Path]:
    files = [tmp_path / f"{name}.md" for name in ("a", "b", "c")]
    for file in files:
        file.write_text(file.stem, "utf-8")
    app.presenter.choose_tool(Tool.MERGE)
    app.presenter.add_paths(files)
    pump(app, seconds=0.1)
    return files


def select(app: TtkApp, index: int) -> None:
    tree = app.main.inputs.tree
    tree.selection_set(tree.get_children()[index])
    pump(app, seconds=0.05)


def test_merge_moves_the_selected_row_and_keeps_it_selected(app: TtkApp, tmp_path: Path) -> None:
    merge_three(app, tmp_path)
    up, down = app.main.move_up, app.main.move_down
    assert up.winfo_ismapped() and down.winfo_ismapped()
    assert (up.cget("text"), down.cget("text")) == ("▲ Move Up", "▼ Move Down")
    assert app.main.order.hint.winfo_ismapped()
    assert "merged in this order" in app.main.order.hint.cget("text")
    assert up.instate(["disabled"]) and down.instate(["disabled"])  # nothing selected
    select(app, 0)
    assert up.instate(["disabled"]) and down.instate(["!disabled"])  # the first cannot go up
    select(app, 2)
    assert up.instate(["!disabled"]) and down.instate(["disabled"])  # the last cannot go down
    up.invoke()
    pump(app, seconds=0.05)
    assert app.main.inputs.names() == ["a.md", "c.md", "b.md"]
    assert app.main.inputs.selected()[0].name == "c.md"  # still selected, in its new place
    tree = app.main.inputs.tree
    tree.focus_set()
    tree.event_generate("<Alt-Up>")  # the keyboard's way: Alt+Up
    pump(app, seconds=0.05)
    assert app.main.inputs.names() == ["c.md", "a.md", "b.md"]


def test_convert_and_split_show_no_order(app: TtkApp, tmp_path: Path) -> None:
    merge_three(app, tmp_path)
    for tool in (Tool.CONVERT, Tool.SPLIT):
        app.presenter.go_to(HOME)
        app.presenter.choose_tool(tool)
        pump(app, seconds=0.05)
        assert not app.main.move_up.winfo_manager() and not app.main.move_down.winfo_manager()
        assert not app.main.order.hint.winfo_manager()


def what_next(app: TtkApp, tmp_path: Path) -> KeepInputsDialog:
    app.presenter.add_paths([tmp_path])
    app.presenter.analyze()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    confirm(app)
    pump(app, until=lambda: app.presenter.page == 4)
    assert app.actions.secondary.cget("text") == "What Next?"
    app.actions.secondary.invoke()
    dialog = app.dialog
    assert isinstance(dialog, KeepInputsDialog)
    return dialog


def test_what_next_goes_home_with_the_files(app: TtkApp, tmp_path: Path) -> None:
    dialog = what_next(app, tmp_path)
    texts = [b.cget("text") for b in (dialog.keep, dialog.clear, dialog.home)]
    assert texts == ["Keep Them", "Start Empty", "Go Back Home"]
    dialog.home.invoke()
    pump(app, seconds=0.05)
    assert app.dialog is None and app.presenter.page == HOME
    assert app.main.inputs.names() == [f"{tmp_path.name}/"]  # going Home keeps the files


def test_what_next_starts_empty(app: TtkApp, tmp_path: Path) -> None:
    what_next(app, tmp_path).clear.invoke()
    pump(app, seconds=0.05)
    assert app.presenter.page == 1 and app.main.inputs.names() == []


def test_no_button_keeps_the_focus_of_the_press_that_opened_a_page(
    app: TtkApp, tmp_path: Path
) -> None:
    app.presenter.add_paths([tmp_path])
    app.root.deiconify()
    primary = app.actions.primary
    primary.focus_force()
    pump(app, until=lambda: app.root.focus_get() is primary, seconds=2)
    primary.invoke()  # Next: Review opens
    pump(app, until=lambda: app.presenter.page == 2)
    pump(app, seconds=0.1)
    assert app.root.focus_get() is not primary and not primary.instate(["focus"])


def test_split_at_the_smallest_window_keeps_rows_in_the_list(app: TtkApp, tmp_path: Path) -> None:
    files = [tmp_path / f"{n}.pdf" for n in range(3)]
    for file in files:
        file.write_bytes(b"%PDF")
    app.root.geometry("800x624")
    app.presenter.choose_tool(Tool.SPLIT)
    app.presenter.add_paths(files)
    pump(app, seconds=0.6)
    tree = app.main.inputs.tree
    assert tree.winfo_height() >= 3 * 36  # the heading and two rows at least
    assert app.main._output.area.scrolls  # the card scrolls instead of taking the list's room
    cuts = app.main.split.cuts
    assert cuts["words"].winfo_rooty() > cuts["parts"].winfo_rooty()  # wrapped: two, then one
    assert cuts["pages"].winfo_rooty() == cuts["parts"].winfo_rooty()


def test_split_at_the_default_size_does_not_scroll_even_in_spanish(app: TtkApp) -> None:
    app.presenter.save_settings(replace(app.presenter.settings, language="es"))
    app.root.geometry("1080x720")
    app.presenter.choose_tool(Tool.SPLIT)
    app.presenter.add_paths([Path("/docs/a.pdf")])
    pump(app, seconds=0.6)
    assert not app.main._output.area.scrolls  # "Results Go" and all, without a scroll
    assert app.main.inputs.tree.winfo_height() >= 2 * 36  # the heading and a whole row


def test_the_drop_zone_s_words_wrap_in_a_narrow_window(app: TtkApp) -> None:
    app.presenter.save_settings(replace(app.presenter.settings, language="es"))
    app.root.geometry("800x624")
    app.presenter.choose_tool(Tool.SPLIT)
    pump(app, seconds=0.6)
    zone = app.main.drop_zone
    texts = [item for item in zone.find_all() if str(zone.type(item)) == "text"]
    words = next(item for item in texts if zone.itemcget(item, "text") == zone.text())
    x1, _, x2, _ = zone.bbox(words)
    assert 0 <= x1 and x2 <= zone.winfo_width()  # inside the zone: wrapped, not cut
