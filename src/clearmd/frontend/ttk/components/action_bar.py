"""The bar at the foot of every page (ADR-0029): the page's primary action, why it is disabled,
and one secondary action (Back, Cancel or Convert more)."""

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from clearmd.frontend.presenter.models import Primary
from clearmd.frontend.ttk.brand import HINT, PAGE, PRIMARY, SOFT, STRONG
from clearmd.frontend.ttk.layout import GAP, SPACE


class ActionBar(ttk.Frame):
    def __init__(self, parent: tk.Misc, *, on_primary: Callable[[], None]) -> None:
        super().__init__(parent, style=PAGE)
        self.primary = ttk.Button(self, style=PRIMARY, command=on_primary)
        self.primary.pack(side="right")
        # One command for the whole life of the button: configuring a new one on every state
        # change would leave a Tcl command behind each time (adversarial check of 007, A7-2).
        self.secondary = ttk.Button(self, style=SOFT, command=self._secondary)
        self.hint = ttk.Label(self, style=HINT, anchor="e", justify="right")
        self.hint.pack(side="right", fill="x", expand=True, padx=(0, GAP))
        self._secondary_command: Callable[[], None] | None = None

    def _secondary(self) -> None:
        if self._secondary_command is not None:
            self._secondary_command()

    def show(self, primary: Primary) -> None:
        self.primary.configure(text=primary.label)
        self.primary.state(["!disabled"] if primary.enabled else ["disabled"])
        self.hint.configure(text=primary.hint)

    def show_secondary(
        self, text: str | None, command: Callable[[], None] | None = None, *, strong: bool = False
    ) -> None:
        """One secondary action next to the primary one, or none (``text`` is None)."""
        if text is None or command is None:
            self.secondary.pack_forget()
            return
        self._secondary_command = command
        self.secondary.configure(text=text, style=STRONG if strong else SOFT)
        if not self.secondary.winfo_ismapped():
            self.secondary.pack(side="right", padx=(0, SPACE), after=self.primary)
