"""Merge (feature 026, AC-05): the third tile of Home, How to Merge on step 1 in place of the
images, each choice calling the presenter, and the Settings group."""

from typing import Any

import pytest
from support.ttk_unit import pump

from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.views import dialogs
from clearmd.frontend.ttk.window import controls


def test_the_third_tile_opens_step_1_of_merge(app: TtkApp) -> None:
    tiles = app.home.tiles
    assert list(tiles) == [Tool.CONVERT, Tool.SPLIT, Tool.MERGE]
    assert tiles[Tool.MERGE].texts()[0] == "Merge Documents"
    pump(app, seconds=0.2)
    widths = [tile.winfo_width() for tile in tiles.values()]
    assert max(widths) - min(widths) <= 1  # one row, all as wide (a pixel of rounding)
    assert len({tile.winfo_rooty() for tile in tiles.values()}) == 1
    tiles[Tool.MERGE].choose()
    pump(app, seconds=0.05)
    assert (app.presenter.page, app.presenter.tool) == (1, Tool.MERGE)
    assert app.surface.header()["title"] == "Choose What to Merge"
    assert app.rail.step_texts()[2] == "Merge"


def test_how_to_merge_shows_only_for_merge(app: TtkApp) -> None:
    app.presenter.choose_tool(Tool.MERGE)
    pump(app, seconds=0.05)
    block = app.main.merge
    assert block.winfo_ismapped() and not app.main.split.winfo_manager()
    assert not app.main.pictures.winfo_manager()  # in place of the images
    assert app.main.summary_buttons[0].winfo_ismapped()  # the summary's choice stays
    assert [b.cget("text") for b in block.choices.values()] == [
        "One Markdown", "One PDF (PDF files only)",
    ]  # fmt: skip
    for tool in (Tool.SPLIT, Tool.CONVERT):
        app.presenter.go_to(0)
        app.presenter.choose_tool(tool)
        pump(app, seconds=0.05)
        assert not block.winfo_manager()
    assert app.main.pictures.winfo_ismapped()


def test_each_choice_calls_choose_split_with_into(
    app: TtkApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    app.presenter.choose_tool(Tool.MERGE)
    seen: list[dict[str, Any]] = []
    real = app.presenter.choose_split

    def recorded(**choice: Any) -> None:
        seen.append(choice)
        real(**choice)

    monkeypatch.setattr(app.presenter, "choose_split", recorded)
    block = app.main.merge
    block.choices["pdf"].invoke()
    assert app.presenter.settings.merge_into == "pdf" and block.into.get() == "pdf"
    block.choices["markdown"].invoke()
    assert seen == [{"into": "pdf"}, {"into": "markdown"}]
    assert app.presenter.settings.merge_into == "markdown"
    controls.apply_enabled(frozenset(), app.main, app.rail)  # as while the work runs
    assert all(control.instate(["disabled"]) for control in block.controls)


def test_settings_round_trips_merge_into(app: TtkApp) -> None:
    app.presenter.go_to(1)
    app.rail.settings.invoke()
    pump(app, seconds=0.2)
    dialog = app.dialog
    assert isinstance(dialog, dialogs.settings.SettingsDialog)
    assert dialog.merge.into.get() == "One Markdown"
    dialog.merge.into.set("One PDF (PDF files only)")
    dialog.save()
    pump(app, seconds=0.1)
    assert app.presenter.settings.merge_into == "pdf"
    app.rail.settings.invoke()
    pump(app, seconds=0.2)
    assert isinstance(app.dialog, dialogs.settings.SettingsDialog)
    assert app.dialog.merge.into.get() == "One PDF (PDF files only)"
    app.dialog.restore()
    assert app.dialog.merge.into.get() == "One Markdown"
    app.dialog.close()
