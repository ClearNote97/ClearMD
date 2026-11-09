"""What the user does without a pointer on a button: Enter and space, Ctrl+1..4, dropped files."""

from collections.abc import Callable
from pathlib import Path
from tkinter import ttk
from typing import Any

from tkinterdnd2 import DND_FILES

from clearmd.frontend.presenter import Action, Presenter
from clearmd.frontend.ttk.window.presses import Presses
from clearmd.frontend.ttk.window.shown import Shown


class Inputs:
    def __init__(
        self,
        root: Any,
        presenter: Presenter,
        shown: Shown,
        press_primary: Callable[[], None],
        primary: ttk.Button,
        *,
        drops: bool,
    ) -> None:
        self._root = root
        self._presenter = presenter
        self._shown = shown
        self._press_primary = press_primary
        self._primary = primary
        self._drops = drops
        self._presses = Presses()

    def bind(self) -> None:
        # Files and folders dropped anywhere on the window (tkinterdnd2, ADR-0026).
        if self._drops:
            self._root.drop_target_register(DND_FILES)
            self._root.dnd_bind("<<Drop>>", self.dropped)
        self._root.bind("<KeyPress-Return>", self.enter)
        self._root.bind("<KeyRelease-Return>", self._presses.released)
        # Space on the focused primary button: held, it is one press too (F-1).
        self._primary.bind("<KeyPress-space>", self.space)
        self._primary.bind("<KeyRelease-space>", self._presses.released)
        for number in range(5):  # the rail by keyboard (AC-01); Ctrl+0: Home (feature 023)
            self._root.bind(
                f"<Control-Key-{number}>", lambda _event, n=number: self._presenter.go_to(n)
            )

    def dropped(self, event: Any) -> None:  # tkinterdnd2's event: ``data`` holds the paths
        paths = [Path(item) for item in self._root.tk.splitlist(event.data)]
        if self._shown.state is not None and Action.ADD in self._shown.state.enabled:
            self._presenter.add_paths(paths)

    def enter(self, event: Any) -> str | None:
        """One keyboard rule (UX §6, audit v3 F2-03): Enter on a button presses that button; in
        a field it confirms the field (its own binding); only otherwise the primary action."""
        focused = self._root.focus_get()
        if isinstance(focused, ttk.Entry):  # a field, a number field, a combo box
            return None
        if not self._presses.pressed(event):  # held down: one press, whatever the page (F-1)
            return None
        if isinstance(focused, ttk.Button) and focused is not self._primary:
            if focused.instate(["!disabled"]):
                focused.invoke()
            return "break"
        self._press_primary()
        return None

    def space(self, event: Any) -> str | None:
        return None if self._presses.pressed(event) else "break"  # "break": the button stays
