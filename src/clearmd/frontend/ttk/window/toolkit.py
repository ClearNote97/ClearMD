"""The Tk root and what ttkbootstrap needs from it. A module of its own: this is the one place that
knows the toolkit's start-up quirks (drag and drop, the default root, the leftover style)."""

import contextlib
import tkinter as tk
from typing import Any

import ttkbootstrap as tb
from PIL import ImageTk
from tkinterdnd2 import TkinterDnD

from clearmd.frontend.design.metrics import MIN_HEIGHT, MIN_WIDTH
from clearmd.frontend.ttk.layout.fonts import make_fonts
from clearmd.frontend.ttk.layout.units import START_SIZE
from clearmd.frontend.ttk.visuals import marks
from clearmd.frontend.ttk.visuals.look import Look
from clearmd.frontend.ttk.visuals.themes import register_themes

_APP_ICON_SIZES = (16, 32, 48, 64, 128, 256)


def root_with_drop() -> Any:
    """A Tk root that accepts dropped files, or a plain one if tkdnd cannot be loaded."""
    try:
        return TkinterDnD.Tk()
    except (RuntimeError, tk.TclError):
        # Its Tk interpreter was created before tkdnd failed, and it is now tkinter's default
        # root: images made without a master would go there. It is closed first.
        stale = getattr(tk, "_default_root", None)
        if stale is not None:
            stale.destroy()
        root: Any = tk.Tk()
        root.TkdndVersion = None
        return root


def prepare(root: Any) -> tuple[tb.Style, dict[str, Any], Look]:
    """The root hidden, sized and made tkinter's default root; its ttkbootstrap style, with the
    two themes registered, the named fonts and the look that installs the styles."""
    root.withdraw()  # shown once laid out, in its theme (no flash of the wrong one)
    root.minsize(MIN_WIDTH, MIN_HEIGHT)
    root.geometry(START_SIZE)
    forget_dead_style()
    # ttkbootstrap speaks to tkinter's default root, not to the one it is given: this window
    # is it, so its styles and messages (Tcl's msgcat) are made in this interpreter, never in
    # one left by an earlier window (CI on Windows, Python 3.12).
    tk._default_root = root  # type: ignore[attr-defined]
    # ttkbootstrap calls Tcl's msgcat without loading it: it works only when Tk happened to
    # load it first, which a new interpreter on Windows does not always do (CI, 014).
    with contextlib.suppress(tk.TclError):
        root.tk.call("package", "require", "msgcat")
    style = tb.Style()
    register_themes(style)
    fonts = make_fonts(root)
    return style, fonts, Look(style, root, fonts)


def forget_dead_style() -> None:
    """ttkbootstrap keeps one Style per process, tied to the first root: a new root (a reopened
    window, a test) needs a new one once that root is gone."""
    existing = tb.Style.instance
    if existing is None:
        return
    try:
        alive = bool(existing.master.winfo_exists())
    except tk.TclError:
        alive = False
    if not alive:
        tb.Style.instance = None


def set_icons(root: Any) -> list[ImageTk.PhotoImage]:
    """The window's icon, in every size; the caller keeps the list (Tk forgets an image Python
    does not hold)."""
    icons = [
        ImageTk.PhotoImage(marks.logo(f"clearmd-app-{size}"), master=root)
        for size in _APP_ICON_SIZES
    ]
    root.iconphoto(True, *icons)
    return icons
