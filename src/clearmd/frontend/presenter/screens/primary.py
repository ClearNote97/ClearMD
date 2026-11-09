"""The page's primary action (Next, Next, Convert, Open results folder): its text, whether it is
enabled and, when it is not, why."""

from collections.abc import Sequence
from pathlib import Path

from clearmd.backend.schemas.models import BatchPlan, BatchReport
from clearmd.frontend.presenter.models import Primary
from clearmd.frontend.presenter.screens.results import result_folders
from clearmd.frontend.presenter.state import HOME, WORKING, AppState, Tool
from clearmd.i18n import Catalog


def primary_of(
    catalog: Catalog,
    page: int,
    state: AppState,
    inputs: Sequence[Path],
    plan: BatchPlan | None,
    report: BatchReport | None,
    tool: Tool = Tool.CONVERT,
) -> Primary:
    text = catalog.text
    ready = state is AppState.WAITING_DECISION and bool(plan and plan.conversions)
    if tool is Tool.MERGE and plan is not None and len(plan.conversions) < 2:
        ready = False  # Merge joins two documents at least: said before, not at the end (B4-01)

    def why() -> str:
        if state is AppState.ANALYZING:
            return text("gui.nav.analyzing")
        if state is AppState.CONVERTING:
            return text("gui.nav.converting")
        if state is AppState.WAITING_DECISION:
            if tool is Tool.MERGE and plan is not None and plan.conversions:
                return text("gui.nav.merge_one_left")
            return text("gui.nav.nothing")
        if report is not None:
            return text("gui.nav.done", more=text("gui.result.again"))
        if not inputs:  # what is missing first, as Choose says it (feature 011)
            return text("gui.nav.need_inputs_first")
        return text("gui.nav.need_plan")

    if page == HOME:  # the start screen has its tiles, no primary action (feature 023)
        return Primary("", False)
    if page == 1:
        if state in WORKING:
            return Primary(text("gui.nav.next"), False, why())
        if not inputs:
            return Primary(text("gui.nav.next"), False, text("gui.nav.need_inputs"))
        if tool is Tool.MERGE and len(inputs) == 1 and not inputs[0].is_dir():
            return Primary(text("gui.nav.next"), False, text("gui.nav.merge_needs_two"))
        return Primary(text("gui.nav.next"), True)
    if page == 2:
        return Primary(text("gui.nav.next"), ready, "" if ready else why())
    if page == 3:
        return Primary(text("gui.main.convert"), ready, "" if ready else why())
    has_results = bool(result_folders(report))
    if has_results:
        hint = ""
    elif state in WORKING:
        hint = why()
    elif report is not None:  # a batch ran and wrote nothing (review of 011)
        hint = text("gui.nav.nothing_written", more=text("gui.result.again"))
    elif not inputs:
        hint = text("gui.nav.need_inputs_first")
    else:
        hint = text("gui.nav.no_results")
    return Primary(text("gui.result.open"), has_results, hint)
