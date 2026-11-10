"""Dropping the plan and the result: an edit (ADR-0029) and an unexpected error. Functions of
their own: inputs, preferences, results and both kinds of work all reach for them."""

from dataclasses import replace
from datetime import datetime

from clearmd.backend.schemas.models import BatchReport
from clearmd.frontend.presenter.display import Display
from clearmd.frontend.presenter.models import ResultView
from clearmd.frontend.presenter.screens.details import details_text
from clearmd.frontend.presenter.screens.results import result_view
from clearmd.frontend.presenter.session import Session
from clearmd.frontend.presenter.state import WORKING, AppState
from clearmd.frontend.presenter.version import app_version
from clearmd.i18n import printable


def editable(session: Session, display: Display) -> bool:
    """Inputs and output change outside the work only; a change drops a plan or a result
    (it was made from the inputs as they were, ADR-0029)."""
    if session.state in WORKING:
        return False
    if session.state is not AppState.READY:
        had_result = session.report is not None
        session.stopped = None
        session.plan = None
        session.report = None
        session.state = AppState.READY
        display.view.forget_work()
        if session.page in (2, 3, 4):  # an edit from Review or Results: back to step 1 (F1-01)
            session.page = 1
            if had_result:  # the files on disk stay as they are; the window says so
                session.notice = session.catalog.text("gui.app.result_kept")
    return True


def shown_result(session: Session, state: AppState) -> ResultView:
    """Results as they are, and after an unexpected error never "0 converted" beside "what was
    converted is kept" (audit v3, F1-05), also when it is drawn again (a new language, v4 F1-01)."""
    assert session.report is not None
    view = result_view(session.catalog, session.report, state)
    if session.stopped is None:
        return view
    done, total = session.stopped
    counts = session.catalog.text("gui.result.stopped_by_error", done=done, total=total)
    return replace(view, counts=counts, stats=())


def unexpected(session: Session, display: Display, error: Exception) -> None:
    """A calm message; the technical line only behind "Copy Details", without paths (D3)."""
    detail = printable(f"{type(error).__name__}: {error}")
    message = session.catalog.text("gui.app.unexpected_error")
    chosen = [
        *session.inputs,
        *(i.source for i in (session.plan.conversions if session.plan else ())),
    ]
    names = [part for path in chosen for part in (path.name, path.stem)]
    session.details = details_text(session.catalog, app_version(), display.view, detail, names)
    session.cancel = None
    plan = session.plan if session.state is AppState.CONVERTING else None
    session.plan = None
    session.report = None
    display.view.forget_work()
    if plan is not None:  # Results, with the folders that may hold what was written (F1-02)
        folders = tuple(dict.fromkeys(item.output_root for item in plan.conversions))
        now = datetime.now()
        session.report = BatchReport(now, now, (), (), (), False, folders=folders)
        state = AppState.FINISHED_WITH_PROBLEMS
        session.stopped = (session.done, len(plan.conversions))
        display.view.show_result(shown_result(session, state))
        session.page = 4
        display.set_state(state)
    else:
        display.set_state(AppState.READY)
    display.view.show_message(message)  # after the state: a view may clear it on a step change
    display.view.show_details_button(session.catalog.text("gui.app.copy_details"))


def copy_details(session: Session, display: Display) -> None:
    """Copy what the error's report needs, then say so (D3); a failing clipboard says nothing."""
    if session.details is None:
        return
    try:
        display.view.copy_text(session.details)
    except Exception:  # noqa: BLE001 -- the error's message stays as it was
        return
    display.view.show_details_button(None)
    display.view.show_message(session.catalog.text("gui.app.details_copied"))
