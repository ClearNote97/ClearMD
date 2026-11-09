"""Feature 039 on the flet window (audit v3): one keyboard rule (AC-10), a row's tone kept when
selected and Results choosing no row for the user (AC-07), Clear All apart (AC-10) and Settings
within a 1366 x 768 screen (AC-09). The window runs on a page that is not flet's, on the
presenter's fake backend."""

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import cast

import flet as ft
import pytest
from support.flet_acceptance import QUIET, Window, click, converted, page_of, pump, windows
from support.gui_fakes import FakeBackend, MemoryBackend

from clearmd.backend.schemas.models import OutcomeStatus
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.flet import FletApp
from clearmd.frontend.flet.views.dialogs.settings import SettingsDialog
from clearmd.frontend.flet.views.dialogs.welcome import WelcomeDialog
from clearmd.frontend.flet.views.results import _TONES
from clearmd.frontend.flet.visuals.theme import role
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.models import Tone
from clearmd.frontend.presenter.state import Tool
from clearmd.i18n import load_catalog


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def focus(control: ft.BaseControl) -> None:
    """The control takes the keyboard focus, as Flutter tells the window."""
    cast(Callable[[], None], getattr(control, "on_focus"))()  # noqa: B009


def listed(flet_window: Window, tool: Tool = Tool.CONVERT) -> FletApp:
    app = flet_window(FakeBackend(settings=QUIET))
    app.presenter.choose_tool(tool)
    app.presenter.add_paths([Path("/docs/a.pdf"), Path("/docs/b.pdf")])
    return app


def to_review(app: FletApp) -> None:
    click(app.actions.primary)
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION, seconds=30)


def test_ac_10_keyboard_enter_on_back_does_not_convert(flet_window: Window) -> None:
    app = listed(flet_window)
    to_review(app)
    app.presenter.go_to(3)
    focus(app.actions.secondary)  # Back has the focus: Enter is Back's (Flutter presses it)
    page_of(app).press("Enter")
    assert app.presenter.state is AppState.WAITING_DECISION and app.presenter.page == 3


def test_ac_10_keyboard_enter_in_a_number_field_does_not_convert(flet_window: Window) -> None:
    app = listed(flet_window, Tool.SPLIT)
    focus(app.main.split.parts.field)
    page_of(app).press("Enter")
    assert app.presenter.state is AppState.READY and app.presenter.page == 1


def test_ac_10_keyboard_delete_and_ctrl_a_in_a_number_field_leave_the_list(
    flet_window: Window,
) -> None:
    app = listed(flet_window, Tool.SPLIT)
    app.main.inputs.toggle(0)
    focus(app.main.split.parts.field)
    page_of(app).press("Delete")
    page_of(app).press("a", ctrl=True)
    assert len(app.main.inputs.rows()) == 2 and len(app.main.inputs.selected()) == 1


def test_ac_10_keyboard_the_list_focused_keeps_its_keys_and_enter(flet_window: Window) -> None:
    app = listed(flet_window)
    box = app.main.inputs.lines[1].box
    assert box is not None
    focus(box)
    page_of(app).press("a", ctrl=True)  # the list has the focus: Ctrl+A checks every row
    assert len(app.main.inputs.selected()) == 2
    page_of(app).press("Enter")  # and Enter still runs the primary action (Next)
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION, seconds=30)
    assert app.presenter.page == 2


def test_ac_10_clear_all_stands_apart_and_last(flet_window: Window) -> None:
    app = listed(flet_window)
    row = app.main.editing.controls
    main = app.main
    assert row.index(main.remove) < row.index(main.deselect) < row.index(main.clear)
    assert row[-1] is main.clear  # alone at the row's right end, as in Qt
    apart = row[row.index(main.clear) - 1]
    assert isinstance(apart, ft.Container) and apart.expand  # the room between them
    assert main.clear.style == main.deselect.style  # still a text button


def test_ac_07_a_selected_row_keeps_its_tone(flet_window: Window) -> None:
    statuses = {"a.pdf": OutcomeStatus.FAILED}
    app = flet_window(FakeBackend(settings=QUIET, statuses=statuses))
    app.presenter.choose_tool(Tool.CONVERT)
    app.presenter.add_paths([Path("/docs")])
    to_review(app)
    app.presenter.confirm(False)
    pump(app, until=lambda: converted(app) and app.presenter.page == 4, seconds=30)
    problems = app.results.problems
    assert problems.current() is None and app.results.detail.value == ""  # none chosen
    line = problems.lines[0]
    border = line.frame.border
    assert isinstance(border, ft.Border) and border.left.color == role("danger")
    click(line.frame)  # selected: the mark stays; the text reads on the selection
    assert problems.current() is not None and line.frame.border is border
    assert all(text.color == role("text") for text in line.texts)
    problems.clear_selection()
    assert all(text.color == role("danger") for text in line.texts)


def test_ac_09_settings_fit_a_1366_by_768_screen(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    page_of(app).resize(1366, 768)
    click(app.rail.settings)
    dialog = app.dialogs.current
    assert isinstance(dialog, SettingsDialog)
    assert dialog.body.scroll == ft.ScrollMode.AUTO  # its rows scroll inside the dialog
    actions = dialog.control.actions or []
    assert dialog.foot in actions and dialog.foot not in dialog.body.controls  # fixed at the foot
    shown = {c.content for c in dialog.foot.controls if isinstance(c, ft.Button)}
    assert load_catalog("en").text("gui.settings.save") in shown


# --- Brief B: the presenter-driven part ---------------------------------------------------------


def test_ac_10_undo_gives_the_list_back(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    app.presenter.choose_tool(Tool.MERGE)
    app.presenter.add_paths([Path("/docs/a.md"), Path("/docs/b.md"), Path("/docs/c.md")])
    paths = [row.payload for row in app.main.inputs.rows()]
    app.presenter.move_input(paths[2], -1)  # Merge's order: a, c, b
    before = [row.name for row in app.main.inputs.rows()]
    catalog = load_catalog("en")
    click(app.main.clear)
    line = app.message_line
    assert app.main.inputs.rows() == ()
    assert line.text.value == catalog.text("gui.main.cleared", count=3)
    assert line.undo.visible and line.undo.content == catalog.text("gui.main.undo")
    assert line.undo.height is not None and line.undo.height >= 44  # a comfortable target
    assert isinstance(line.undo, ft.Button)  # reached by Tab, as every button
    click(line.undo)
    assert [row.name for row in app.main.inputs.rows()] == before == ["a.md", "c.md", "b.md"]
    assert not line.undo.visible and not line.control.visible


def test_ac_04_the_welcome_switches_the_language(flet_window: Window) -> None:
    backend = MemoryBackend(Settings())  # a first run: the Welcome opens
    app = flet_window(backend)
    pump(app, until=lambda: app.dialogs.current is not None)
    dialog = app.dialogs.current
    assert isinstance(dialog, WelcomeDialog)
    en, es = load_catalog("en"), load_catalog("es")
    assert dialog.languages["en"].content == en.text("gui.welcome.language_en") == "English"
    assert dialog.languages["es"].content == es.text("gui.welcome.language_es") == "Español"
    assert dialog.title.value == en.text("gui.welcome.title")
    click(dialog.languages["es"])
    assert backend.settings.language == "es" and app.dialogs.current is dialog  # still open
    assert dialog.title.value == es.text("gui.welcome.title")
    assert es.text("gui.welcome.step1") in dialog.texts()
    assert dialog.languages["en"].content == "English"  # each in its own language
    assert app.rail.home_text().removeprefix("> ") == es.text("gui.home.step")  # the window too


def test_ac_04_results_say_how_to_use_it(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    app.presenter.choose_tool(Tool.CONVERT)
    app.presenter.add_paths([Path("/docs")])
    to_review(app)
    app.presenter.confirm(False)
    pump(app, until=lambda: converted(app) and app.presenter.page == 4, seconds=30)
    result = app.shown.last_result
    assert result is not None and result.with_ai == load_catalog("en").text("gui.result.with_ai")
    line = app.results.with_ai
    assert line.visible and line.value == result.with_ai
    assert line.max_lines is None  # wrapped, never cut
    assert line.color == role("muted")


def test_ac_07_left_outs_with_nothing_to_do_are_not_alarms(flet_window: Window) -> None:
    assert _TONES[Tone.NEUTRAL] == "" and _TONES[Tone.DANGER] == "danger"  # plain text, no mark
    app = flet_window(FakeBackend(settings=QUIET))
    assert app.results.problems_title.color == role("warning")  # what needs attention
