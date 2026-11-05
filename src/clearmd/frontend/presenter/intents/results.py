"""After a batch: open the result folders, or go back to Choose to convert more."""

from clearmd.frontend.presenter.display import Display
from clearmd.frontend.presenter.ports import Backend
from clearmd.frontend.presenter.screens.results import result_folders
from clearmd.frontend.presenter.session import Session
from clearmd.frontend.presenter.state import WORKING, AppState
from clearmd.i18n import printable


class Results:
    def __init__(self, session: Session, display: Display, backend: Backend) -> None:
        self._session = session
        self._display = display
        self._backend = backend

    def convert_more(self, *, keep: bool) -> None:
        """From the results to Choose again, with the chosen files or without them."""
        s = self._session
        if s.state in WORKING:
            return
        s.plan = None
        s.report = None
        self._display.view.forget_work()  # nothing of the last batch stays on screen (007, A7-1)
        if not keep:
            s.inputs.clear()
        s.page = 1
        self._display.show_inputs()
        self._display.set_state(AppState.READY)

    def open_results(self) -> None:
        problems = []
        for folder in result_folders(self._session.report):
            try:
                self._backend.open_folder(folder)
            except (OSError, ValueError):
                path = printable(str(folder))
                problems.append(self._session.catalog.text("gui.result.cannot_open", path=path))
        if problems:  # every one of them: a later message would hide an earlier one
            self._display.view.show_message("\n".join(problems))
