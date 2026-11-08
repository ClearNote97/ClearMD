"""One dialog at a time: help, settings, welcome, and the question after Convert more."""

from PySide6.QtWidgets import QWidget

from clearmd.frontend.presenter import Action, Presenter
from clearmd.frontend.pyside.components.dialog import Dialog
from clearmd.frontend.pyside.views.dialogs.help import HelpDialog
from clearmd.frontend.pyside.views.dialogs.keep_inputs import KeepInputsDialog
from clearmd.frontend.pyside.views.dialogs.settings import SettingsDialog
from clearmd.frontend.pyside.views.dialogs.welcome import WelcomeDialog
from clearmd.frontend.pyside.window.shown import Shown


class DialogHost:
    def __init__(self, parent: QWidget, presenter: Presenter, shown: Shown) -> None:
        self._parent = parent
        self._presenter = presenter
        self._shown = shown
        self.current: Dialog | None = None  # the open dialog: one at a time

    def convert_more(self) -> None:
        """Results' "What Next?", asked every time: keep the files, start empty or go back Home
        (features 007, 032)."""
        if self.current is None:
            self._open(
                KeepInputsDialog(
                    self._parent,
                    self._shown.need_catalog(),
                    on_answer=self._presenter.what_next,
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

    def _open(self, dialog: Dialog) -> None:
        self.current = dialog
        dialog.open()  # modal, without a nested event loop

    def _closed(self) -> None:
        self.current = None
