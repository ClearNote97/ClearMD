"""The lists (feature 007, T03)."""

import time
from pathlib import Path

import pytest
from support.ttk_unit import pump

from clearmd.frontend.presenter import AppState
from clearmd.frontend.ttk import TtkApp

# --- Lists (feature 007, T03) --------------------------------------------------------------------


def checked(app: TtkApp) -> list[bool]:
    return app.main.inputs.checked()


def test_rows_have_a_checkbox_that_follows_the_selection(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path / "b.pdf", tmp_path / "c.pdf"])
    tree = app.main.inputs.tree
    assert checked(app) == [False, False, False]
    tree.selection_set(tree.get_children()[1])
    pump(app, seconds=0.05)
    assert checked(app) == [False, True, False]
    app.main.inputs.toggle(tree.get_children()[2])  # a click on a row's box adds it
    pump(app, seconds=0.05)
    assert checked(app) == [False, True, True]


def test_the_header_box_selects_all_and_clears_all(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path / "b.pdf"])
    app.main.inputs.toggle_all()
    pump(app, seconds=0.05)
    assert checked(app) == [True, True]
    app.main.inputs.toggle_all()
    pump(app, seconds=0.05)
    assert checked(app) == [False, False]


def test_deselect_all_and_a_click_on_empty_space_clear_the_selection(
    app: TtkApp, tmp_path: Path
) -> None:
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path / "b.pdf"])
    tree = app.main.inputs.tree
    tree.selection_set(tree.get_children())
    app.main.deselect.invoke()
    assert tree.selection() == ()
    tree.selection_set(tree.get_children())
    app.root.geometry("1080x900")  # room below the rows, whatever the system's font (Windows)
    pump(app, seconds=0.3)
    tree.event_generate("<Button-1>", x=200, y=tree.winfo_height() - 8)  # below the rows
    pump(app, seconds=0.05)
    assert tree.selection() == ()


def test_the_headings_draw_faint_separators(app: TtkApp) -> None:
    layout = str(app.style.layout("Treeview.Heading"))
    assert "Heading.ClearMD.cell" in layout


def test_review_says_ready_to_convert_for_a_file_without_problems(
    app: TtkApp, tmp_path: Path
) -> None:
    app.presenter.add_paths([tmp_path])
    app.actions.primary.invoke()
    pump(app, until=lambda: app.presenter.page == 2)
    assert app.last_plan is not None
    assert app.last_plan.rows[0].detail == "✓ Ready to convert · PDF"


def test_f1_a_held_or_doubled_enter_never_skips_a_page(
    app: TtkApp, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app.presenter.go_to(1)  # the window opens on Home (feature 023)
    monkeypatch.setattr("clearmd.frontend.presenter.chrome.primary_gate.PRIMARY_PAUSE_SECONDS", 0.5)
    time.sleep(0.6)  # step 1's own pause is over
    app.presenter.add_paths([tmp_path])
    app.primary_button.press()
    pump(app, until=lambda: app.presenter.page == 2)
    time.sleep(0.6)
    app.primary_button.press()  # Review → Convert
    app.primary_button.press()  # at once again: the same burst must not start the batch
    pump(app, seconds=0.05)
    assert app.presenter.page == 3 and app.presenter.state is AppState.WAITING_DECISION
    time.sleep(0.6)
    app.primary_button.press()  # a deliberate press, later, does
    pump(app, until=lambda: app.presenter.page == 4)
    assert app.presenter.page == 4
