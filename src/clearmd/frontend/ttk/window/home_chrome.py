"""What Home (feature 023) changes around the page: no action bar nor message at its foot (its
header, without a step counter, is the presenter's ``header_of``). A module of its own: the view
stays within its size."""

from tkinter import ttk

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
