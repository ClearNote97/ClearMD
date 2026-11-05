"""The first step of the window: choose what to convert (005, T04)."""

from pathlib import Path
from types import SimpleNamespace

from support.ttk_unit import press_enter, pump

from clearmd.frontend.presenter import AppState
from clearmd.frontend.ttk import TtkApp


def test_the_window_shows_the_first_step_with_convert_disabled(app: TtkApp) -> None:
    assert app.root.title() == "ClearMD"
    assert app.surface.header()["eyebrow"] == "Step 1 of 4"
    assert app.surface.header()["title"] == "Choose what to convert"
    assert app.rail.step_texts() == ["> Choose", "Review", "Convert", "Results"]
    assert app.actions.primary.instate(["disabled"])
    assert app.main.remove.instate(["disabled"])


def test_inputs_are_numbered_with_their_icons_and_enable_convert(
    app: TtkApp, tmp_path: Path
) -> None:
    (tmp_path / "a.pdf").write_bytes(b"%PDF")
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path])
    pump(app, seconds=0.2)
    assert app.main.inputs.names() == ["a.pdf", f"{tmp_path.name}/"]
    tree = app.main.inputs.tree
    assert all(tree.item(item, "image") for item in tree.get_children())
    assert not app.main.inputs.empty.winfo_ismapped()
    assert app.actions.primary.instate(["!disabled"])


def test_removing_the_selection_and_clearing(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path / "b.pdf"])
    tree = app.main.inputs.tree
    tree.selection_set(tree.get_children()[0])
    app.main.remove.invoke()
    assert app.main.inputs.names() == ["b.pdf"]
    app.main.clear.invoke()
    assert app.main.inputs.names() == []


def test_dropped_files_and_folders_are_added(app: TtkApp, tmp_path: Path) -> None:
    data = app.root.tk.call("list", str(tmp_path / "a b.pdf"), str(tmp_path))  # a space in a name
    app.inputs.dropped(SimpleNamespace(data=data))
    shown = app.main.inputs.names()
    assert shown[0] == "a b.pdf" and len(shown) == 2


def test_enter_triggers_convert_and_the_rail_moves_to_review(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path])
    press_enter(app)
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    assert app.presenter.state is AppState.WAITING_DECISION
    assert app.last_plan is not None
    assert app.rail.step_texts()[1] == "> Review"
    assert app.surface.header()["eyebrow"] == "Step 2 of 4 · Waiting for your decision"
