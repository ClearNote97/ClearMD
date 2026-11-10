"""Feature 040 on the flet window (audit v4): the whole "what to do" in the row, and the arrows in
Review's and Results' lists (AC-05); colours that agree with Qt and ttk (AC-10); a keyboard focus
that shows (AC-11). The window runs on a page that is not flet's; strings come from the catalog
and the presenter's own builders."""

from collections.abc import Iterator
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import flet as ft
import pytest
from support.flet_acceptance import QUIET, Window, click, converted, page_of, pump, windows
from support.gui_fakes import FakeBackend, planned

from clearmd.backend.schemas.errors import ErrorCode
from clearmd.backend.schemas.models import BatchPlan, BatchReport, ConversionOutcome, OutcomeStatus
from clearmd.frontend.flet import FletApp
from clearmd.frontend.flet.components.rail_art import rail_style
from clearmd.frontend.flet.visuals.look import DEFAULT, FOCUSED, button_style, tile_style
from clearmd.frontend.flet.visuals.theme import role
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.screens.results import result_view
from clearmd.frontend.presenter.state import Tool
from clearmd.i18n import load_catalog


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def run(app: FletApp) -> None:
    app.presenter.choose_tool(Tool.CONVERT)
    app.presenter.add_paths([Path("/docs")])
    click(app.actions.primary)
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION, seconds=30)
    app.presenter.confirm(False)
    pump(app, until=lambda: converted(app) and app.presenter.page == 4, seconds=30)


def test_ac_05_the_whole_what_to_do_is_in_the_row(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=replace(QUIET, language="es")))
    page_of(app).resize(800, 624)
    run(app)
    crashed = ConversionOutcome(planned("informe.pdf"), OutcomeStatus.FAILED,
                                ErrorCode.WORKER_CRASHED)  # fmt: skip
    now = datetime.now()
    report = BatchReport(now, now, (crashed,), (), (), False)
    view = result_view(load_catalog("es"), report, AppState.FINISHED_WITH_PROBLEMS)
    app.view.show_result(view)  # the longest "what to do", as the presenter builds it
    detail = view.rows[0].detail
    assert len(detail.split()) > 40  # the hard case: the crash with its {report}
    line = app.results.problems.lines[0]
    shown = line.texts[1]
    assert shown.value == detail  # the whole text, in the row itself
    assert shown.max_lines is None  # wrapped on as many lines as it takes
    assert shown.overflow is not ft.TextOverflow.ELLIPSIS  # never cut with "…"
    assert line.frame.height is None  # the row grows with its text
    assert app.results.problems.current() is None  # never chosen for the user


def test_ac_05_the_arrows_move_in_results_and_review(flet_window: Window) -> None:
    statuses = {"a.pdf": OutcomeStatus.FAILED, "c.pdf": OutcomeStatus.FAILED}
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf"), planned("c.pdf")), (), ())
    app = flet_window(FakeBackend(settings=QUIET, plan=plan, statuses=statuses))
    run(app)
    page = page_of(app)
    problems = app.results.problems
    page.press("Arrow Down")  # none selected: the first
    assert problems.current() == problems.rows()[0] and page.revealed[-1] == 0
    page.press("Arrow Down")
    assert problems.current() == problems.rows()[1] and page.revealed[-1] == 1
    page.press("Arrow Down")  # the last stays
    page.press("Arrow Up")
    assert problems.current() == problems.rows()[0]
    assert app.results.detail.value  # the selected row's detail follows
    app.presenter.go_to(2)
    files = app.review.files
    page.press("Arrow Down")
    assert files.current() == files.rows()[1]  # Review had its first problem (or first) selected


def test_ac_10_the_eyebrow_warns_and_the_figures_keep_their_tones(flet_window: Window) -> None:
    statuses = {"a.pdf": OutcomeStatus.FAILED}
    app = flet_window(FakeBackend(settings=QUIET, statuses=statuses))
    run(app)
    assert app.presenter.state is AppState.FINISHED_WITH_PROBLEMS
    assert app.surface.eyebrow.color == role("warning")  # as Qt and ttk
    result = app.shown.last_result
    assert result is not None
    expected = {"accent": "accent_text", "warning": "warning", "danger": "danger"}
    for (figure, _name), stat in zip(app.results.stats._cards, result.stats, strict=True):
        assert figure.color == role(expected.get(stat.tone.value, "text"))  # as sent
    clean = flet_window(FakeBackend(settings=QUIET))  # all went well: the usual colour
    run(clean)
    assert clean.presenter.state is AppState.FINISHED
    assert clean.surface.eyebrow.color == role("accent_text")


def sides(style: ft.ButtonStyle) -> tuple[object, object]:
    side = style.side
    assert isinstance(side, dict)
    return side.get(FOCUSED), side.get(DEFAULT)


@pytest.mark.parametrize(
    "style",
    [
        button_style(""),
        button_style("strong"),
        button_style("primary"),
        button_style("link"),
        tile_style(),
        tile_style(current=True),
        rail_style(),
        rail_style(current=True),
    ],
)
def test_ac_11_every_control_shows_the_keyboard_focus(style: ft.ButtonStyle) -> None:
    """flet's styles take the theme's roles: one check holds for both themes."""
    focused, rest = sides(style)
    assert isinstance(focused, ft.BorderSide) and focused.width >= 2
    assert focused != rest  # the focus differs from the control at rest
    assert isinstance(style.side, dict) and next(iter(style.side)) is FOCUSED  # wins over hover


def test_ac_11_the_last_used_tile_and_the_focused_one_differ() -> None:
    last_used, _ = sides(tile_style(current=True))
    _, last_used_at_rest = sides(tile_style(current=True))
    assert last_used != last_used_at_rest
