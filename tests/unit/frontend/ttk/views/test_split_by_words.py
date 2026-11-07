"""Split's third cut, parts of about N words (feature 024, AC-05): on step 1 and in Settings."""

from typing import Any

import pytest
from support.ttk_unit import pump

from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.views import dialogs


def split(app: TtkApp) -> None:
    app.presenter.choose_tool(Tool.SPLIT)
    pump(app, seconds=0.05)


def type_in(app: TtkApp, field: Any, text: str) -> None:
    """Type ``text`` in a number field and press Enter (key events go to the focus)."""
    app.root.deiconify()
    field.focus_force()
    pump(app, until=lambda: app.root.focus_get() is field, seconds=2)
    field.delete(0, "end")
    field.insert(0, text)
    field.event_generate("<Return>", when="tail")
    pump(app, seconds=0.05)


def test_the_third_cut_and_the_hint_are_shown(app: TtkApp) -> None:
    split(app)
    block = app.main.split
    assert list(block.cuts) == ["parts", "pages", "words"]  # the same order in every window
    assert block.cuts["words"].cget("text") == "Parts of about"
    assert block.numbers["words"].get() == "30000"
    assert block.hint.winfo_ismapped()
    assert block.hint.cget("text").startswith("About: an AI reads a limited amount of text")


def test_the_words_radio_and_field_call_choose_split(
    app: TtkApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    split(app)
    seen: list[dict[str, Any]] = []
    real = app.presenter.choose_split

    def recorded(**choice: Any) -> None:
        seen.append(choice)
        real(**choice)

    monkeypatch.setattr(app.presenter, "choose_split", recorded)
    block = app.main.split
    block.cuts["words"].invoke()
    type_in(app, block.numbers["words"], "8000")
    block.numbers["words"].event_generate("<<Increment>>")  # the arrows step by a thousand
    assert seen == [{"cut": "words"}, {"words": 8000}, {"words": 9000}]
    settings = app.presenter.settings
    assert (settings.split_cut, settings.split_words) == ("words", 9000)
    assert block.cut.get() == "words"


def test_a_refused_number_of_words_shows_the_stored_one_again(app: TtkApp) -> None:
    split(app)
    field = app.main.split.numbers["words"]
    for typed in ("499", "lots", "1000001"):  # words are 500..1,000,000
        type_in(app, field, typed)
        assert field.get() == "30000", typed
    assert app.presenter.settings.split_words == 30_000


def test_settings_round_trips_the_words(app: TtkApp) -> None:
    app.presenter.go_to(1)
    app.rail.settings.invoke()
    pump(app, seconds=0.2)
    dialog = app.dialog
    assert isinstance(dialog, dialogs.settings.SettingsDialog)
    group = dialog.split
    group.cut.set("words")
    group.numbers["words"].delete(0, "end")
    group.numbers["words"].insert(0, "12000")
    dialog.save()
    pump(app, seconds=0.1)
    assert (app.presenter.settings.split_cut, app.presenter.settings.split_words) == (
        "words",
        12000,
    )
    app.rail.settings.invoke()
    pump(app, seconds=0.2)
    assert isinstance(app.dialog, dialogs.settings.SettingsDialog)
    again = app.dialog.split
    assert again.cut.get() == "words" and again.numbers["words"].get() == "12000"
    again.numbers["words"].delete(0, "end")
    again.numbers["words"].insert(0, "100")  # out of range: the loaded value stays
    app.dialog.save()
    pump(app, seconds=0.1)
    assert app.presenter.settings.split_words == 12000
