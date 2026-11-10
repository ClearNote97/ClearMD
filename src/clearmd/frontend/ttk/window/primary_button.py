"""The page's primary action and its pause after a page change (UX §6, ADR-0029)."""

import time
import tkinter as tk

from clearmd.frontend.presenter import Presenter
from clearmd.frontend.presenter.chrome import primary_gate
from clearmd.frontend.ttk.components.action_bar import ActionBar
from clearmd.frontend.ttk.views.review import ReviewView
from clearmd.frontend.ttk.window.dialog_host import DialogHost
from clearmd.frontend.ttk.window.shown import Shown


class PrimaryButton:
    def __init__(
        self,
        root: tk.Misc,
        actions: ActionBar,
        review: ReviewView,
        presenter: Presenter,
        dialogs: DialogHost,
        shown: Shown,
    ) -> None:
        self._root = root
        self._actions = actions
        self._review = review
        self._presenter = presenter
        self._dialogs = dialogs
        self._shown = shown
        self._page_shown_at = 0.0  # when the page on screen changed (F-1)
        self._unpause: str | None = None  # the end of that pause

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
        if self._unpause is not None:
            self._root.after_cancel(self._unpause)
            self._unpause = None
        pause = primary_gate.pause_milliseconds()
        if pause == 0:
            return
        # Even when the button is disabled now (an analysis): a quick one must not enable it
        # before the pause is over (seen on Windows CI, 040).
        self._actions.primary.state(["disabled"])
        self._unpause = self._root.after(pause, self._end_pause)

    def hold(self) -> None:
        """A state shown during the pause (its page unchanged) leaves the button disabled."""
        if self._unpause is not None:
            self._actions.primary.state(["disabled"])

    def cancel_pause(self) -> None:
        if self._unpause is not None:
            self._root.after_cancel(self._unpause)
            self._unpause = None

    def _end_pause(self) -> None:
        self._unpause = None
        if self._shown.state is not None:
            self._actions.show(self._shown.state.primary)
