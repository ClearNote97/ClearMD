"""A dialog in ClearMD's look (ADR-0027): modal, over the window, a title, a card, its buttons.

Esc closes it, like its Close/Cancel button (UX §6); the window's own icon is inherited.
"""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from tkinter import ttk

from clearmd.frontend.ttk.brand import CARD, ON_PAGE, PAGE, Palette
from clearmd.frontend.ttk.layout import GAP, MARGIN


class Dialog(tk.Toplevel):
    """``body`` is the card to fill; ``actions`` the row of buttons below it, right-aligned."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        title: str,
        palette: Palette,
        fonts: dict[str, tkfont.Font],
        on_close: Callable[[], None],
        width: int = 640,
    ) -> None:
        super().__init__(
            parent,
            background=palette.ground,
            highlightthickness=1,  # a hairline edge, under any window manager
            highlightbackground=palette.border,
            highlightcolor=palette.border,
        )
        self.title(title)
        self.transient(parent.winfo_toplevel())
        self.resizable(False, False)
        self._on_close = on_close
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", lambda _event: self.close())

        frame = ttk.Frame(self, style=PAGE, padding=MARGIN, width=width)
        frame.pack(fill="both", expand=True)
        self.heading = ttk.Label(frame, text=title, font=fonts["title"], style=ON_PAGE)
        self.heading.pack(anchor="w")
        self.body = ttk.Frame(frame, style=CARD, padding=MARGIN)
        self.body.pack(fill="both", expand=True, pady=(GAP, 0))
        self.actions = ttk.Frame(frame, style=PAGE)
        self.actions.pack(fill="x", pady=(GAP, 0))

    def open(self) -> None:
        """Centre it over the window, show it, and keep the focus in it until it closes."""
        self.update_idletasks()
        parent = self.master.winfo_toplevel()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_reqwidth()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.deiconify()
        try:
            self.wait_visibility()
            self.grab_set()
        except tk.TclError:  # not viewable (a minimized window), or closed while waiting
            pass
        if self.winfo_exists():
            self.focus_set()

    def close(self) -> None:
        self.grab_release()
        self.destroy()
        self._on_close()
