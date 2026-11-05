"""Helpers of the ttk window unit tests (a window under a display, pumped by hand)."""

import time
from collections.abc import Iterator
from typing import Any

from clearmd.frontend.ttk import TtkApp


def pump(window: TtkApp, *, until: Any = None, seconds: float = 2.0) -> None:
    """Run the UI loop for a moment (or until ``until()`` holds)."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        window.root.update()
        if until is not None and until():
            return
        time.sleep(0.01)


def confirm(app: TtkApp) -> None:
    """Convert the plan: Next on Review, then Convert (ADR-0029)."""
    if app.presenter.page == 2:
        app.actions.primary.invoke()
    app.actions.primary.invoke()


def convert_more(app: TtkApp, *, keep: bool = True) -> None:
    from clearmd.frontend.ttk.views.dialogs.keep_inputs import KeepInputsDialog

    app.actions.secondary.invoke()
    assert isinstance(app.dialog, KeepInputsDialog)
    app.dialog.answer(keep)


def press_enter(app: TtkApp) -> None:
    """Enter on the window: it needs the keyboard focus first (Windows gives it only on demand)."""
    app.root.focus_force()
    app.root.update()
    app.root.event_generate("<KeyPress-Return>", when="tail")
    app.root.event_generate("<KeyRelease-Return>", when="tail")  # pressed and let go


def widgets(root: Any) -> Iterator[Any]:
    pending = [root]
    while pending:
        widget = pending.pop()
        yield widget
        pending.extend(widget.winfo_children())


def shown(app: TtkApp) -> object:
    """The page on screen (typed loosely: tests compare it with several views)."""
    return app.page
