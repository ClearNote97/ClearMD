"""The page's primary action (Next, Next, Convert, Open results folder): its text, whether it is
enabled and, when it is not, why."""

from collections.abc import Sequence
from pathlib import Path

from clearmd.backend.schemas.models import BatchPlan, BatchReport
from clearmd.frontend.presenter.models import Primary
from clearmd.frontend.presenter.screens.results import result_folders
from clearmd.frontend.presenter.state import WORKING, AppState
from clearmd.i18n import Catalog


def primary_of(
    catalog: Catalog,
    page: int,
    state: AppState,
    inputs: Sequence[Path],
    plan: BatchPlan | None,
    report: BatchReport | None,
) -> Primary:
    text = catalog.text
    ready = state is AppState.WAITING_DECISION and bool(plan and plan.conversions)

    def why() -> str:
        if state is AppState.ANALYZING:
            return text("gui.nav.analyzing")
        if state is AppState.CONVERTING:
            return text("gui.nav.converting")
        if state is AppState.WAITING_DECISION:
            return text("gui.nav.nothing")
        if report is not None:
            return text("gui.nav.done")
        if not inputs:  # what is missing first, as Choose says it (feature 011)
            return text("gui.nav.need_inputs_first")
        return text("gui.nav.need_plan")

    if page == 1:
        if state in WORKING:
            return Primary(text("gui.nav.next"), False, why())
        if not inputs:
            return Primary(text("gui.nav.next"), False, text("gui.nav.need_inputs"))
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
        hint = text("gui.nav.nothing_written")
    elif not inputs:
        hint = text("gui.nav.need_inputs_first")
    else:
        hint = text("gui.nav.no_results")
    return Primary(text("gui.result.open"), has_results, hint)
