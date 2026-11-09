"""Dropping the plan and the result: an edit (ADR-0029) and an unexpected error. Functions of
their own: inputs, preferences, results and both kinds of work all reach for them."""

from clearmd.frontend.presenter.display import Display
from clearmd.frontend.presenter.screens.details import details_text
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
        session.plan = None
        session.report = None
        session.state = AppState.READY
        display.view.forget_work()
    return True


def unexpected(session: Session, display: Display, error: Exception) -> None:
    """A calm message; the technical line only behind "Copy Details", without paths (D3)."""
    detail = printable(f"{type(error).__name__}: {error}")
    message = session.catalog.text("gui.app.unexpected_error")
    session.details = details_text(session.catalog, app_version(), display.view, detail)
    session.cancel = None
    session.plan = None
    session.report = None
    display.view.forget_work()
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
