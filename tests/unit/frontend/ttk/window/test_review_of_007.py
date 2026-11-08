"""Regressions found in the code review of 007 (C7-*)."""

from pathlib import Path

from support.ttk_unit import pump

from clearmd.frontend.ttk import TtkApp

# --- Code review of 007 (C7-*) -------------------------------------------------------------------


def test_c7_1_after_an_edit_review_convert_and_results_are_emptied(
    app: TtkApp, tmp_path: Path
) -> None:
    app.presenter.add_paths([tmp_path])
    app.primary_button.press()
    pump(app, until=lambda: app.presenter.page == 2)
    app.presenter.add_paths([tmp_path / "more.pdf"])
    assert app.review.files.names() == [] and app.review.stats.dimmed  # waiting, faded (014)
    assert {value for _, value in app.review.stats.figures()} == {"—"}


def test_c7_2_the_smallest_window_shows_every_control(app: TtkApp, tmp_path: Path) -> None:
    app.root.geometry("800x624")
    app.presenter.add_paths([tmp_path / f"{n}.pdf" for n in range(30)])
    pump(app, seconds=0.4)
    assert app.main.output_label.winfo_ismapped() and app.main.next_to.winfo_ismapped()
    bottom = app.main.output_label.winfo_rooty() + app.main.output_label.winfo_height()
    assert bottom <= app.actions.winfo_rooty()


def test_c7_5_enter_in_what_next_runs_the_focused_tile(app: TtkApp) -> None:
    from clearmd.frontend.presenter.state import Tool
    from clearmd.frontend.ttk.views.dialogs.what_next import WhatNextDialog

    app.presenter.add_paths([Path("/docs")])
    app.dialogs.what_next()
    dialog = app.dialog
    assert isinstance(dialog, WhatNextDialog)
    tile = dialog.tiles[Tool.MERGE]
    tile.focus_force()
    pump(app, until=lambda: dialog.focus_get() is tile, seconds=2)
    tile.event_generate("<Return>", when="tail")
    pump(app, until=lambda: app.dialog is None, seconds=1)
    assert app.presenter.tool is Tool.MERGE  # the tile with the focus (033)
    assert app.main.inputs.names()  # the box was ticked: the files are kept


def test_c7_6_the_rail_is_drawn_again_only_when_the_page_changes(app: TtkApp) -> None:
    app.presenter.go_to(1)  # the window opens on Home (feature 023)
    calls: list[int] = []
    real = app.rail._draw

    def counted() -> None:
        calls.append(1)
        real()

    app.rail._draw = counted  # type: ignore[method-assign]
    app.presenter.add_paths([Path("/docs/a.pdf")])  # the state changes, the page does not
    assert calls == []


def test_c7_7_space_checks_a_row_and_ctrl_a_selects_all(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path / "b.pdf"])
    tree = app.main.inputs.tree
    app.root.deiconify()
    tree.focus_force()
    tree.focus(tree.get_children()[1])
    pump(app, until=lambda: app.root.focus_get() is tree, seconds=2)
    tree.event_generate("<space>", when="tail")
    pump(app, seconds=0.05)
    assert app.main.inputs.checked() == [False, True]
    tree.event_generate("<Control-a>", when="tail")
    pump(app, seconds=0.05)
    assert app.main.inputs.checked() == [True, True]
