"""Closing the window (AC-10): while converting, cancel, hide and wait for the batch to end."""

import time

from PySide6.QtCore import QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QWidget

from clearmd.frontend.presenter import Presenter
from clearmd.frontend.presenter.chrome import close_policy
from clearmd.frontend.pyside.window.dialog_host import DialogHost
from clearmd.frontend.pyside.window.primary_button import PrimaryButton
from clearmd.frontend.pyside.window.scheduler import Scheduler
from clearmd.frontend.pyside.window.shown import Shown


class Closing:
    def __init__(
        self,
        window: QWidget,
        presenter: Presenter,
        shown: Shown,
        scheduler: Scheduler,
        dialogs: DialogHost,
        primary_button: PrimaryButton,
    ) -> None:
        self._window = window
        self._presenter = presenter
        self._shown = shown
        self._scheduler = scheduler
        self._dialogs = dialogs
        self._primary_button = primary_button
        self._closing_since: float | None = None  # closed while converting: waiting for the end
        self.closed = False

    def close_event(self, event: QCloseEvent) -> None:
        """Qt's close: the window closes only when this has run its course."""
        if self.closed:
            event.accept()
            return
        event.ignore()
        self.close()

    def close(self) -> None:
        """Closing while converting cancels, hides the window and waits for the batch to end, so
        the summary of what was done is still written; then the window closes."""
        if self._closing_since is not None or self.closed:
            return
        if self._dialogs.current is not None:
            self._dialogs.current.close_dialog()  # its answer counts ("Don't show again")
        self._presenter.shutdown()
        state = self._shown.state
        step = close_policy.on_close(state.state if state is not None else None)
        if step is close_policy.CloseStep.CANCEL_AND_WAIT:
            self._closing_since = time.monotonic()
            self._presenter.cancel()
            self._window.hide()
            QTimer.singleShot(close_policy.CLOSE_POLL_MS, self._close_when_done)
            return
        if step is close_policy.CloseStep.CANCEL_THEN_NOW:
            self._presenter.cancel()
        self.destroy()

    def _close_when_done(self) -> None:
        waited = time.monotonic() - (self._closing_since or 0.0)
        state = self._shown.state
        if close_policy.keep_waiting(state.state if state is not None else None, waited):
            QTimer.singleShot(close_policy.CLOSE_POLL_MS, self._close_when_done)
            return
        self.destroy()

    def destroy(self) -> None:
        self._scheduler.close()
        self._primary_button.cancel_pause()
        self.closed = True
        self._window.close()
