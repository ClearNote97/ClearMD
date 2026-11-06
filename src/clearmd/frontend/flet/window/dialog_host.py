"""One dialog at a time: help, settings, welcome, and the question after Convert more."""

from collections.abc import Callable
from typing import Any

from clearmd.frontend.flet.components.dialog import Dialog
from clearmd.frontend.flet.views.dialogs.help import HelpDialog
from clearmd.frontend.flet.views.dialogs.keep_inputs import KeepInputsDialog
from clearmd.frontend.flet.views.dialogs.settings import SettingsDialog
from clearmd.frontend.flet.views.dialogs.welcome import WelcomeDialog
from clearmd.frontend.flet.window.focus import Focus
from clearmd.frontend.flet.window.page_port import PagePort
from clearmd.frontend.flet.window.shown import Shown
from clearmd.frontend.presenter import Action, Presenter


class DialogHost:
    def __init__(self, page: PagePort, presenter: Presenter, shown: Shown, focus: Focus) -> None:
        self._page = page
        self._focus = focus
        self._presenter = presenter
        self._shown = shown
        self.current: Dialog | None = None  # the open dialog: one at a time

    def convert_more(self) -> None:
        """Asked every time: keep the chosen files, or start empty (feature 007)."""
        if self.current is None:
            self._open(
                KeepInputsDialog(
                    self._shown.need_catalog(),
                    on_answer=lambda keep: self._sent(self._presenter.convert_more, keep=keep),
                    on_close=self._closed,
                )
            )

    def show_help(self) -> None:
        """The "?" window: always available (UX §4)."""
        if self.current is None:
            self._open(
                HelpDialog(
                    self._shown.need_catalog(), self._closed, version=self._presenter.version
                )
            )

    def show_settings(self) -> None:
        if self.current is not None or not self._shown.allows(Action.SETTINGS):
            return
        if self._shown.state is None:
            return
        self._open(
            SettingsDialog(
                self._shown.need_catalog(),
                self._presenter.settings,
                on_save=lambda chosen: self._sent(self._presenter.save_settings, chosen),
                on_close=self._closed,
            )
        )

    def welcome(self, steps: tuple[str, ...]) -> None:
        if self.current is not None:
            return

        def done(show_again: bool) -> None:
            self._closed()
            self._sent(self._presenter.dismiss_welcome, show_again=show_again)

        self._open(WelcomeDialog(self._shown.need_catalog(), steps, done))

    def _open(self, dialog: Dialog) -> None:
        self.current = dialog
        dialog.dismiss = lambda: self._page.close_dialog(dialog.control)
        self._focus.forget()  # the window's controls are behind the dialog now
        self._focus.watch(dialog.control)
        self._page.show_dialog(dialog.control)

    def _sent(self, action: Callable[..., None], *args: Any, **kwargs: Any) -> None:
        """A dialog's answer, then the page to the screen. Closing the dialog already updated
        flet's page, so flet sends nothing more after the click: without this, what the answer
        changed (Choose again, a new theme) showed only at the next click (v1.0.1)."""
        action(*args, **kwargs)
        self._page.refresh()

    def _closed(self) -> None:
        self.current = None
        self._focus.forget()
