"""One dialog at a time: help, settings, welcome, and the question after Convert more."""

import tkinter as tk
from typing import Any

from clearmd.frontend.presenter import Action, Presenter
from clearmd.frontend.ttk.components.dialog import Dialog
from clearmd.frontend.ttk.views.dialogs.help import help_dialog
from clearmd.frontend.ttk.views.dialogs.keep_inputs import KeepInputsDialog
from clearmd.frontend.ttk.views.dialogs.settings import SettingsDialog
from clearmd.frontend.ttk.views.dialogs.welcome import WelcomeDialog
from clearmd.frontend.ttk.window.shown import Shown


class DialogHost:
    def __init__(
        self, root: tk.Misc, fonts: dict[str, Any], presenter: Presenter, shown: Shown
    ) -> None:
        self._root = root
        self._fonts = fonts
        self._presenter = presenter
        self._shown = shown
        self.current: Dialog | None = None  # the open dialog: one at a time

    def convert_more(self) -> None:
        """Results' "What Next?", asked every time: keep the files, start empty, or go Home."""
        if self.current is not None:
            return
        dialog = KeepInputsDialog(
            self._root,
            self._shown.need_catalog(),
            self._shown.palette,
            self._fonts,
            on_answer=lambda answer: self._presenter.what_next(answer),
            on_close=self._closed,
        )
        self._open(dialog)

    def show_help(self) -> None:
        """The "?" window: always available (UX §4)."""
        if self.current is None:
            self._open(
                help_dialog(
                    self._root,
                    self._shown.need_catalog(),
                    self._shown.palette,
                    self._fonts,
                    self._closed,
                    version=self._presenter.version,
                )  # fmt: skip
            )

    def show_settings(self) -> None:
        if self.current is not None or self._shown.state is None:
            return
        if Action.SETTINGS not in self._shown.state.enabled:
            return
        dialog = SettingsDialog(
            self._root,
            self._shown.need_catalog(),
            self._shown.palette,
            self._fonts,
            self._presenter.settings,
            on_save=self._presenter.save_settings,
            on_close=self._closed,
        )
        self._open(dialog)

    def welcome(self, steps: tuple[str, ...]) -> None:
        if self.current is not None:
            return

        def done(show_again: bool) -> None:
            self._closed()
            self._presenter.dismiss_welcome(show_again=show_again)

        dialog = WelcomeDialog(
            self._root, self._shown.need_catalog(), self._shown.palette, self._fonts, steps, done
        )
        self._open(dialog)

    def _open(self, dialog: Dialog) -> None:
        self.current = dialog
        dialog.open()

    def _closed(self) -> None:
        self.current = None
