"""One dialog at a time: help, settings, welcome, Results' "What Next?", and the question when the
window is closed during a task."""

from collections.abc import Callable

from PySide6.QtWidgets import QWidget

from clearmd.frontend.presenter import Action, Presenter
from clearmd.frontend.pyside.components.dialog import Dialog
from clearmd.frontend.pyside.views.dialogs.confirm_close import ConfirmCloseDialog
from clearmd.frontend.pyside.views.dialogs.help import HelpDialog
from clearmd.frontend.pyside.views.dialogs.settings import SettingsDialog
from clearmd.frontend.pyside.views.dialogs.welcome import WelcomeDialog
from clearmd.frontend.pyside.views.dialogs.what_next import WhatNextDialog
from clearmd.frontend.pyside.window.shown import Shown


class DialogHost:
    def __init__(self, parent: QWidget, presenter: Presenter, shown: Shown) -> None:
        self._parent = parent
        self._presenter = presenter
        self._shown = shown
        self.current: Dialog | None = None  # the open dialog: one at a time

    def what_next(self) -> None:
        """Results' "What Next?", asked every time: a tool, and whether the files stay (033)."""
        if self.current is None:
            presenter = self._presenter
            self._open(
                WhatNextDialog(
                    self._parent,
                    self._shown.need_catalog(),
                    presenter.next_choices(),
                    colour=self._shown.palette.accent_text,
                    on_choose=lambda tool, keep: presenter.continue_with(tool, keep=keep),
                    on_close=self._closed,
                )
            )

    def show_help(self) -> None:
        """The "?" window: always available (UX §4)."""
        if self.current is None:
            self._open(
                HelpDialog(
                    self._parent,
                    self._shown.need_catalog(),
                    self._closed,
                    version=self._presenter.version,
                )
            )

    def show_settings(self) -> None:
        if self.current is not None or not self._shown.allows(Action.SETTINGS):
            return
        if self._shown.state is None:
            return
        self._open(
            SettingsDialog(
                self._parent,
                self._shown.need_catalog(),
                self._presenter.settings,
                on_save=self._presenter.save_settings,
                on_close=self._closed,
            )
        )

    def welcome(self, steps: tuple[str, ...]) -> None:
        if self.current is not None:
            return

        def done(show_again: bool) -> None:
            self._closed()
            self._presenter.dismiss_welcome(show_again=show_again)

        self._open(WelcomeDialog(self._parent, self._shown.need_catalog(), steps, done))

    def confirm_close(self, on_close_window: Callable[[], None]) -> None:
        """Closing during a task: asked once (audit v2, F1-01); another dialog gives way."""
        if isinstance(self.current, ConfirmCloseDialog):
            return
        if self.current is not None:
            self.current.close_dialog()
        self._open(
            ConfirmCloseDialog(
                self._parent,
                self._shown.need_catalog(),
                on_close_window=on_close_window,
                on_close=self._closed,
            )
        )

    def _open(self, dialog: Dialog) -> None:
        self.current = dialog
        dialog.open()  # modal, without a nested event loop

    def _closed(self) -> None:
        self.current = None
