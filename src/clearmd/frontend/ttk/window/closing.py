"""Closing the window (AC-10): while converting, ask once (038), then cancel, hide and wait for
the batch to end; in every other state the window closes at once, without asking."""

import time
from typing import Any

from clearmd.frontend.presenter import Presenter
from clearmd.frontend.presenter.chrome import close_policy
from clearmd.frontend.ttk.window.dialog_host import DialogHost
from clearmd.frontend.ttk.window.primary_button import PrimaryButton
from clearmd.frontend.ttk.window.scheduler import Scheduler
from clearmd.frontend.ttk.window.shown import Shown


class Closing:
    def __init__(
        self,
        root: Any,
        presenter: Presenter,
        shown: Shown,
        scheduler: Scheduler,
        dialogs: DialogHost,
        primary_button: PrimaryButton,
    ) -> None:
        self._root = root
        self._presenter = presenter
        self._shown = shown
        self._scheduler = scheduler
        self._dialogs = dialogs
        self._primary_button = primary_button
        self._closing_since: float | None = None  # closed while converting: waiting for the end

    def close(self, *, confirmed: bool = True) -> None:
        """The window's X asks first while converting (``confirmed=False``, 038: Keep Working is
        the default); a close the code asks for is already decided. Confirmed, it
        cancels, hides the window and waits for the batch to end, so the summary of what was
        done is still written (AC-10); then the window closes."""
        if self._closing_since is not None:
            return
        state = self._shown.state
        step = close_policy.on_close(state.state if state is not None else None)
        if step is close_policy.CloseStep.CANCEL_AND_WAIT and not confirmed:
            self._dialogs.confirm_close(lambda: self.close(confirmed=True))
            return
        if self._dialogs.current is not None:
            self._dialogs.current.close()  # its answer counts ("Don't show again")
        self._presenter.shutdown()
        if step is close_policy.CloseStep.CANCEL_AND_WAIT:
            self._closing_since = time.monotonic()
            self._presenter.cancel()
            self._root.withdraw()
            self._root.after(close_policy.CLOSE_POLL_MS, self._close_when_done)
            return
        if step is close_policy.CloseStep.CANCEL_THEN_NOW:
            self._presenter.cancel()
        self.destroy()

    def _close_when_done(self) -> None:
        waited = time.monotonic() - (self._closing_since or 0.0)
        state = self._shown.state
        if close_policy.keep_waiting(state.state if state is not None else None, waited):
            self._root.after(close_policy.CLOSE_POLL_MS, self._close_when_done)
            return
        self.destroy()

    def destroy(self) -> None:
        self._primary_button.cancel_pause()
        self._scheduler.close()
        self._root.update_idletasks()  # Tk's own idle work (a theme change) runs before the end
        self._root.destroy()
