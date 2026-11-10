"""What changes around a page as it opens: Home (feature 023) has no action bar nor message at its
foot (its header, without a step counter, is the presenter's ``header_of``), and no button keeps
the look of the press that opened the page (032). A module of its own: the view stays within its
size."""

import tkinter as tk
from tkinter import ttk
from typing import Any

from clearmd.frontend.design.metrics import SPACE


def show_bar(actions: ttk.Frame, message: ttk.Label, page: ttk.Frame, *, shown: bool) -> None:
    """The action bar and the message above it; on Home neither: its card takes the room. ``page``
    is the page on screen, which the bar goes below again."""
    if not shown:
        actions.pack_forget()
        message.pack_forget()
    elif not actions.winfo_manager():
        actions.pack(side="bottom", fill="x", pady=(SPACE, 0), before=page)
        message.pack(side="bottom", fill="x", pady=(SPACE, 0), after=actions)


def calm_focus(root: tk.Misc) -> None:
    """A page has just opened: a button (or a tile) that kept the focus of the press that opened
    it would show its focus ring there; the window takes the focus back (Enter still works)."""
    focused = root.focus_get()
    if isinstance(focused, ttk.Button) or getattr(focused, "lit", None) is not None:
        root.focus_set()


def page_changed(root: tk.Misc, message: ttk.Label, actions: Any) -> None:
    """Another page opened: a message belongs to the page it was given on, and so do its
    "Copy Details" (036) and "Undo" (039); no button keeps the press's focus ring (032)."""
    message.configure(text="")
    actions.show_details(None)
    actions.show_undo(None)
    calm_focus(root)
