"""The help dialog (UX §4; feature 035, AC-04): the sections the presenter gives the three windows
(``presenter.screens.help``), titles strong and texts wrapped, in a body that scrolls when the
window is shorter than they are; the version at the foot."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from tkinter import ttk

from clearmd.frontend.design.metrics import GAP, HALF, MIN_HEIGHT
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.presenter.screens.help import help_sections
from clearmd.frontend.ttk.components.dialog import Dialog
from clearmd.frontend.ttk.components.scroll_area import ScrollArea
from clearmd.frontend.ttk.visuals.style_names import HINT, PRIMARY
from clearmd.i18n import Catalog

HELP_WIDTH = 720  # wide and short: it fits a 1366 × 768 screen with its taskbar


class HelpDialog(Dialog):
    """``sections``: the (title, text) labels shown, in order."""

    sections: list[tuple[ttk.Label, ttk.Label]]


def help_dialog(
    parent: tk.Misc,
    catalog: Catalog,
    palette: Palette,
    fonts: dict[str, tkfont.Font],
    on_close: Callable[[], None],
    version: str = "",
    *,
    drops: bool = False,
) -> HelpDialog:
    """Every section of ``help_sections``, in order; ``drops``: this window takes files dropped
    from the system (tkdnd loaded), so the help may say so."""
    dialog = HelpDialog(
        parent,
        title=catalog.text("gui.help.title"),
        palette=palette,
        fonts=fonts,
        on_close=on_close,
    )
    area = ScrollArea(dialog.body, ground=palette.card)
    area.pack(fill="both", expand=True)
    dialog.sections = []
    for index, (title_text, body_text) in enumerate(help_sections(catalog, drops=drops)):
        title = ttk.Label(area.inner, text=title_text, font=fonts["strong"])
        title.pack(anchor="w", pady=(0 if index == 0 else GAP, 0))
        text = ttk.Label(area.inner, text=body_text, wraplength=HELP_WIDTH, justify="left")
        text.pack(anchor="w", pady=(HALF, 0))
        dialog.sections.append((title, text))
    if version:
        shown = catalog.text("gui.help.version", version=version)
        ttk.Label(dialog.actions, text=shown, style=HINT).pack(side="left")
    close = ttk.Button(
        dialog.actions, text=catalog.text("gui.help.close"), style=PRIMARY, command=dialog.close
    )
    close.pack(side="right")
    dialog.bind("<Return>", lambda _event: dialog.close())
    # As tall as the window leaves it (the screen, before the window shows); then it scrolls.
    dialog.update_idletasks()
    window = parent.winfo_toplevel().winfo_height()
    room = window if window > MIN_HEIGHT // 2 else dialog.winfo_screenheight()
    chrome = dialog.winfo_reqheight() - area.winfo_reqheight()
    area.fit(max(room - chrome - 2 * GAP, 12 * GAP))
    area.follow_focus()
    return dialog
