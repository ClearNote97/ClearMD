"""What the user does without a pointer: Enter, Esc, Ctrl+0 (Home) and Ctrl+1..4, Delete and Ctrl+A
on the list. One rule (039, UX §6): Enter on a button presses it, in a field confirms it, and only
otherwise (nothing focused, or the list) runs the primary action; Delete and Ctrl+A act on the list
only while it, or nothing, has the focus.

flet gives every key to the page, not to a control: the window decides here what each does — a
dialog's keys first (Esc closes it, Enter runs its default action), then the window's. Enter is
the focused control's when one has the focus (``focus.py``)."""

from collections.abc import Callable

from clearmd.frontend.flet.views.choose import ChooseView
from clearmd.frontend.flet.window.dialog_host import DialogHost
from clearmd.frontend.flet.window.focus import Focus
from clearmd.frontend.flet.window.page_port import KeyPress
from clearmd.frontend.presenter import Presenter
from clearmd.frontend.presenter.state import HOME, STEPS

ENTER = frozenset({"Enter", "Numpad Enter"})  # the main keyboard's and the keypad's
STEP_KEYS = {str(number): number for number in range(HOME, len(STEPS) + 1)}  # 0: Home (023)


class Keys:
    def __init__(
        self,
        presenter: Presenter,
        dialogs: DialogHost,
        press_primary: Callable[[], None],
        main: ChooseView,
        focus: Focus,
    ) -> None:
        self._focus = focus
        self._presenter = presenter
        self._dialogs = dialogs
        self._press_primary = press_primary
        self._main = main

    def pressed(self, key: KeyPress) -> None:
        dialog = self._dialogs.current
        if dialog is not None:  # the dialog has the keyboard
            if key.key == "Escape":
                dialog.close_dialog()
            elif key.key in ENTER and not self._focus.taken:
                dialog.press_default()
            return
        if key.key in ENTER:
            # A focused button or field takes Enter itself (Flutter); the list does not (039).
            if not self._focus.taken or self._main.inputs.holds(self._focus.holder):
                self._press_primary()
        elif key.ctrl and key.key in STEP_KEYS:  # the rail by keyboard
            self._presenter.go_to(STEP_KEYS[key.key])
        elif self._presenter.page == 1:
            self._on_choose(key)

    def _on_choose(self, key: KeyPress) -> None:
        """The list of Choose: Delete removes the checked files, Ctrl+A checks them all; only
        while the list has the focus or nothing has it (039: a number being typed, or a button,
        keeps its keys)."""
        holder = self._focus.holder
        if holder is not None and not self._main.inputs.holds(holder):
            return
        if key.key == "Delete" and not self._main.remove.disabled:
            self._main.remove_selected()
        elif key.ctrl and key.key.upper() == "A":
            self._main.inputs.select_all()
