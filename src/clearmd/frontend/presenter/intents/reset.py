"""Dropping the plan and the result: an edit (ADR-0029) and an unexpected error. Functions of
their own: inputs, preferences, results and both kinds of work all reach for them."""

from clearmd.frontend.presenter.display import Display
from clearmd.frontend.presenter.session import Session
from clearmd.frontend.presenter.state import WORKING, AppState
from clearmd.i18n import printable


def editable(session: Session, display: Display) -> bool:
    """Inputs and output change outside the work only; a change drops a plan or a result
    (it was made from the inputs as they were, ADR-0029)."""
    if session.state in WORKING:
        return False
    if session.state is not AppState.READY:
        session.plan = None
        session.report = None
        session.state = AppState.READY
        display.view.forget_work()
    return True


def unexpected(session: Session, display: Display, error: Exception) -> None:
    detail = printable(f"{type(error).__name__}: {error}")
    message = session.catalog.text("gui.app.unexpected_error", detail=detail)
    session.cancel = None
    session.plan = None
    session.report = None
    display.view.forget_work()
    display.set_state(AppState.READY)
    display.view.show_message(message)  # after the state: a view may clear it on a step change
