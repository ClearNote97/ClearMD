"""Feature 040 on the ttk window (audit v4): a row's "what to do" shown whole, wrapped inside the
row (AC-05), the colours that agree with the presenter's tones (AC-10), and a keyboard focus you
can see on every control type, in both themes (AC-11). Strings come from the catalog."""

import os
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from PIL import Image, ImageChops, ImageGrab
from support.flet_acceptance import QUIET
from support.gui_fakes import FakeBackend, planned
from support.ttk_unit import confirm, pump

from clearmd.backend.schemas.errors import ErrorCode, SkipReason
from clearmd.backend.schemas.models import (
    BatchPlan,
    ConversionOutcome,
    OutcomeStatus,
    SkippedItem,
)
from clearmd.backend.services.rejections import error_text
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.models import ResultRow, ResultView, Tone
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.components.row_wrap import wrapped
from clearmd.i18n import load_catalog

DOCS = Path("/docs")


def test_ac_05_the_whole_reason_is_in_the_row(window: Callable[..., TtkApp]) -> None:
    app = window(FakeBackend(settings=replace(QUIET, language="es")))
    app.root.geometry("800x624")
    catalog = load_catalog("es")
    outcome = ConversionOutcome(
        planned("informe.pdf"), OutcomeStatus.FAILED, ErrorCode.WORKER_CRASHED
    )
    detail = (
        f"{catalog.text('gui.result.word_failed')} {error_text(catalog, outcome)}"  # the longest
    )
    row = ResultRow("informe.pdf", "/docs", detail, "pdf", Tone.DANGER)
    app.results.show(ResultView("", "", (row,), (DOCS,), ()))
    app.presenter.go_to(4)
    pump(app, seconds=0.5)
    tree = app.results.problems.tree
    (item,) = tree.get_children()
    shown = str(tree.item(item, "values")[0])
    assert "…" not in shown and "".join(shown.split()) == "".join(detail.split())  # all of it
    assert shown.count("\n") >= 1  # wrapped inside the row, which grows
    width = tree.winfo_width() - int(tree.column("#0", "width"))
    font = app.fonts["body"]
    assert all(font.measure(line) <= width for line in shown.split("\n"))  # nothing past the edge
    assert tree.selection() == ()  # Results never pre-selects a row
    assert wrapped("una ruta/muy/larga", 40, font)  # a word longer than a line is cut, not lost


def test_ac_10_the_colours_agree_with_the_tones(window: Callable[..., TtkApp]) -> None:
    plan = BatchPlan(
        (planned("a.pdf"), planned("b.pdf")),
        (SkippedItem(DOCS / "notas.md", SkipReason.ALREADY_MARKDOWN),),  # informative only
        (),
    )
    app = window(FakeBackend(plan=plan, settings=QUIET, statuses={"a.pdf": OutcomeStatus.FAILED}))
    app.presenter.add_paths([DOCS])
    app.presenter.analyze()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    confirm(app)
    pump(app, until=lambda: app.presenter.page == 4)
    pump(app, seconds=0.1)
    assert app.presenter.state is AppState.FINISHED_WITH_PROBLEMS
    assert app.surface._warning  # the counter line in the warning colour, as Qt and flet
    assert app.last_result is not None
    colours = {Tone.ACCENT: app.palette.accent_text, Tone.WARNING: app.palette.warning,
               Tone.DANGER: app.palette.danger, Tone.NEUTRAL: app.palette.text}  # fmt: skip
    drawn = [str(figure.cget("foreground")) for figure, _ in app.results.stats._cards]
    assert drawn == [colours[stat.tone] for stat in app.last_result.stats]  # as sent


def grab(app: TtkApp, widget: Any) -> Image.Image:
    app.root.update()
    x, y = widget.winfo_rootx(), widget.winfo_rooty()
    box = (x, y, x + widget.winfo_width(), y + widget.winfo_height())
    return ImageGrab.grab(bbox=box, xdisplay=os.environ["DISPLAY"]).convert("RGB")


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_ac_11_every_control_shows_its_focus(window: Callable[..., TtkApp], theme: str) -> None:
    app = window(FakeBackend(settings=replace(QUIET, theme=theme)))
    app.root.deiconify()
    app.root.geometry("1080x720+0+0")
    pump(app, seconds=0.3)
    tile = app.home.tiles[Tool.CONVERT]
    check_focus(app, "tile", tile, tile)  # Home's tiles
    app.presenter.choose_tool(Tool.CONVERT)
    app.presenter.add_paths([DOCS / "a.pdf", DOCS / "b.pdf"])
    pump(app, seconds=0.5)
    main, actions = app.main, app.actions
    check_focus(app, "list", main.inputs.tree, main.inputs)  # the card's ring and the row's tint
    check_focus(app, "link", main.remove, main.remove)
    check_focus(app, "button", main.add_files, main.add_files)
    check_focus(app, "primary", actions.primary, actions.primary)
    check_focus(app, "rail", app.rail.settings, app.rail.settings)


def check_focus(app: TtkApp, name: str, widget: Any, shown: Any) -> None:
    app.root.focus_force()
    pump(app, until=lambda: app.root.focus_get() is app.root, seconds=2)
    before = grab(app, shown)
    widget.focus_force()
    pump(app, until=lambda: app.root.focus_get() is widget, seconds=2)
    pump(app, seconds=0.1)
    after = grab(app, shown)
    assert ImageChops.difference(before, after).getbbox() is not None, name  # it looks focused
