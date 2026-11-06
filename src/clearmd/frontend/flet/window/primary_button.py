"""The page's primary action and its pause after a page change (UX §6, ADR-0029)."""

import time

from clearmd.frontend.flet.components.action_bar import ActionBar
from clearmd.frontend.flet.views.review import ReviewView
from clearmd.frontend.flet.window.dialog_host import DialogHost
from clearmd.frontend.flet.window.scheduler import Scheduler
from clearmd.frontend.flet.window.shown import Shown
from clearmd.frontend.presenter import Presenter
from clearmd.frontend.presenter.chrome import primary_gate

UNPAUSE_MARGIN_MS = 10


class PrimaryButton:
    def __init__(
        self,
        actions: ActionBar,
        review: ReviewView,
        presenter: Presenter,
        dialogs: DialogHost,
        shown: Shown,
        scheduler: Scheduler,
    ) -> None:
        self._actions = actions
        self._review = review
        self._presenter = presenter
        self._dialogs = dialogs
        self._shown = shown
        self._scheduler = scheduler
        self._page_shown_at = 0.0  # when the page on screen changed (F-1)
        self._pause = 0  # the pause under way: an earlier one's end does nothing

    def page_shown(self) -> None:
        self._page_shown_at = time.monotonic()

    def press(self) -> None:
        """The page's primary action, from its button or Enter (UX §6, ADR-0029). Right after the
        page changes it waits a moment, shown disabled: a double click must not run Next and
        Convert past a page the user did not see (security audit of 007, F-1)."""
        if self._dialogs.current is not None:
            return
        if not primary_gate.gate_open(self._page_shown_at, time.monotonic()):
            return
        self._presenter.press_primary(self._review.overwrite_answer())

    def pause(self) -> None:
        """The primary button is disabled for the pause after a page change, so it is seen."""
        pause = primary_gate.pause_milliseconds()
        if pause == 0 or self._actions.primary.disabled:
            return
        self._actions.primary.disabled = True
        # Counted from the page change, and a little over: the button is never enabled while
        # its press would still be ignored.
        left = pause - round((time.monotonic() - self._page_shown_at) * 1000)
        self._pause += 1
        token = self._pause
        self._scheduler.after(max(left, 0) + UNPAUSE_MARGIN_MS, lambda: self._end_pause(token))

    def cancel_pause(self) -> None:
        self._pause += 1

    def _end_pause(self, token: int) -> None:
        if token == self._pause and self._shown.state is not None:
            self._actions.show(self._shown.state.primary)
