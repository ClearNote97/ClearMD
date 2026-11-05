"""Feature 005 — The presenter (AC-01 to AC-04); spec/features/005_*/spec.md.

The window runs under a display (a virtual one when there is none), mostly on a fake backend.
"""

import ast
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from support.gui_fakes import FakeBackend, planned
from support.ttk_acceptance import (
    QUIET,
    ROOT,
    confirm,
    converted,
    pump,
    replace_settings,
    to_review,
)

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.models import BatchPlan, SkippedItem
from clearmd.frontend.presenter import Action, AppState
from clearmd.frontend.presenter.models import StateView
from clearmd.frontend.ttk import TtkApp
from clearmd.i18n import load_catalog


def test_ac_01_one_state_at_a_time_and_each_enables_its_actions(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    app = window(FakeBackend(settings=QUIET))
    seen: list[tuple[AppState, frozenset[Action]]] = []
    real = app.show_state

    def recorded(state: StateView) -> None:
        seen.append((state.state, state.enabled))
        real(state)

    app.show_state = recorded  # type: ignore[method-assign]
    assert Action.CONVERT not in (app.state.enabled if app.state else frozenset())
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=lambda: converted(app))
    states = [state for state, _ in seen]
    assert states[:3] == [AppState.READY, AppState.ANALYZING, AppState.WAITING_DECISION]
    assert AppState.CONVERTING in states and states[-1] is AppState.FINISHED
    for state, enabled in seen:
        working = state in {AppState.ANALYZING, AppState.CONVERTING}
        assert (Action.CANCEL in enabled) is working
        assert Action.CONVERT not in enabled or state is AppState.READY


def test_ac_02_the_work_never_runs_on_the_ui_thread(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    ui = threading.get_ident()
    planned_on: list[int] = []
    fake = FakeBackend(settings=QUIET)
    real_plan = fake.plan_batch

    def slow_plan(inputs: Any, **options: Any) -> BatchPlan:
        planned_on.append(threading.get_ident())
        time.sleep(0.5)  # meanwhile the window must keep handling events
        return real_plan(inputs, **options)

    fake.plan_batch = slow_plan  # type: ignore[method-assign]
    app = window(fake)
    ticks: list[float] = []
    app.presenter.add_paths([tmp_path])
    app.actions.primary.invoke()
    for _ in range(10):
        app.root.after(20, lambda: ticks.append(time.monotonic()))
        pump(app, seconds=0.03)
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    assert planned_on and planned_on[0] != ui
    assert len(ticks) >= 5  # the UI loop ran while the plan was being made


def test_ac_03_every_text_comes_from_the_catalogs_in_the_chosen_language(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    plan = BatchPlan(
        (planned("a.pdf"),),
        (SkippedItem(Path("/docs/notas.md"), SkipReason.ALREADY_MARKDOWN),),
        (),
    )
    app = window(FakeBackend(plan=plan, settings=replace_settings(QUIET, language="es")))
    es = load_catalog("es")
    assert app.actions.primary.cget("text") == es.text("gui.nav.next")
    assert app.surface.header()["title"] == es.text("gui.page.choose_title")
    to_review(app, tmp_path)
    (skipped,) = [row for row in app.last_plan.rows if row.name == "notas.md"]  # type: ignore[union-attr]
    assert skipped.detail.startswith(es.text("skip.already_markdown"))


def test_ac_04_the_presenter_imports_only_the_api_schemas_i18n_and_the_standard_library() -> None:
    allowed = (
        "clearmd.backend.api",
        "clearmd.backend.schemas",
        "clearmd.i18n",
        "clearmd.frontend.presenter",
    )
    for path in (ROOT / "src" / "clearmd" / "frontend" / "presenter").rglob("*.py"):  # R01
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom) and node.level == 0
                else []
            )
            for name in names:
                top = name.split(".")[0]
                assert top not in {"tkinter", "turtle"}, (path.name, name)
                assert name.startswith(allowed) or top in sys.stdlib_module_names, (path.name, name)
