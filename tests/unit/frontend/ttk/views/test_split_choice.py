"""Split's step 1 (feature 023, AC-09, AC-10): How to Split in place of the images' choice, each
control calling the presenter, and the Settings group."""

from typing import Any

import pytest
from support.ttk_unit import pump

from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.views import dialogs
from clearmd.frontend.ttk.window import controls


def split(app: TtkApp) -> None:
    app.presenter.choose_tool(Tool.SPLIT)
    pump(app, seconds=0.05)


def calls(app: TtkApp, monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    seen: list[dict[str, Any]] = []
    real = app.presenter.choose_split

    def recorded(**choice: Any) -> None:
        seen.append(choice)
        real(**choice)

    monkeypatch.setattr(app.presenter, "choose_split", recorded)
    return seen


def type_in(app: TtkApp, field: Any, text: str) -> None:
    """Type ``text`` in a number field and press Enter (key events go to the focus)."""
    app.root.deiconify()
    field.focus_force()
    pump(app, until=lambda: app.root.focus_get() is field, seconds=2)
    field.delete(0, "end")
    field.insert(0, text)
    field.event_generate("<Return>", when="tail")
    pump(app, seconds=0.05)


def test_the_split_block_shows_only_for_split_in_place_of_the_images(app: TtkApp) -> None:
    app.presenter.choose_tool(Tool.CONVERT)
    pump(app, seconds=0.05)
    assert not app.main.split.winfo_manager() and app.main.pictures.winfo_ismapped()
    split(app)
    assert app.main.split.winfo_ismapped()
    assert not app.main.pictures.winfo_manager()  # the images' choice is hidden
    note = app.main.split.note.cget("text")
    assert note == "Each part keeps whole pages, in order. Nothing inside them changes."
    assert app.main.summary_buttons[0].winfo_ismapped()  # the summary's choice stays
    app.presenter.go_to(0)
    app.presenter.choose_tool(Tool.CONVERT)
    pump(app, seconds=0.05)
    assert not app.main.split.winfo_manager() and app.main.pictures.winfo_ismapped()


def test_each_control_calls_choose_split(app: TtkApp, monkeypatch: pytest.MonkeyPatch) -> None:
    split(app)
    seen = calls(app, monkeypatch)
    block = app.main.split
    block.cuts["pages"].invoke()
    block.keeps["pdf"].invoke()
    type_in(app, block.numbers["parts"], "4")
    block.numbers["pages"].event_generate("<<Increment>>")  # an arrow commits at once
    assert seen == [{"cut": "pages"}, {"keep": "pdf"}, {"parts": 4}, {"pages": 51}]
    settings = app.presenter.settings
    assert (settings.split_cut, settings.split_keep) == ("pages", "pdf")
    assert (settings.split_parts, settings.split_pages) == (4, 51)


def test_a_refused_number_shows_the_stored_one_again(app: TtkApp) -> None:
    split(app)
    field = app.main.split.numbers["parts"]
    for typed in ("1", "many", "10001"):  # parts are 2..10000
        type_in(app, field, typed)
        assert field.get() == "2", typed
    assert app.presenter.settings.split_parts == 2


def test_the_split_controls_follow_the_output_s_enabled_state(app: TtkApp) -> None:
    split(app)
    assert all(control.instate(["!disabled"]) for control in app.main.split.controls)
    controls.apply_enabled(frozenset(), app.main, app.rail)  # as while the work runs
    assert all(control.instate(["disabled"]) for control in app.main.split.controls)


def test_the_settings_group_round_trips(app: TtkApp) -> None:
    app.presenter.go_to(1)
    app.rail.settings.invoke()
    pump(app, seconds=0.2)
    dialog = app.dialog
    assert isinstance(dialog, dialogs.settings.SettingsDialog)
    group = dialog.split
    assert group.cut.get() == "parts" and group.keep.get() == "Both"
    assert [n.get() for n in group.numbers.values()] == ["2", "50"]
    group.cut.set("pages")
    group.keep.set("Their Markdown")
    group.numbers["pages"].delete(0, "end")
    group.numbers["pages"].insert(0, "20")
    group.numbers["parts"].delete(0, "end")
    group.numbers["parts"].insert(0, "1")  # out of range: the loaded value stays
    dialog.save()
    pump(app, seconds=0.1)
    s = app.presenter.settings
    assert (s.split_cut, s.split_parts, s.split_pages, s.split_keep) == ("pages", 2, 20, "markdown")
    app.rail.settings.invoke()
    pump(app, seconds=0.2)
    assert isinstance(app.dialog, dialogs.settings.SettingsDialog)
    again = app.dialog.split
    assert (again.cut.get(), again.keep.get()) == ("pages", "Their Markdown")
    assert again.numbers["pages"].get() == "20"
    app.dialog.restore()
    assert again.cut.get() == "parts" and again.numbers["pages"].get() == "50"
    app.dialog.close()
