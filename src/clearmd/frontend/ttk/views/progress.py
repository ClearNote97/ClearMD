"""Step 3, Convert: where it is, the time left, and Cancel always at hand (UX §2; AC-09, AC-10)."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from tkinter import ttk
from typing import Any

from PIL import ImageTk

from clearmd.frontend.presenter.models import ProgressView
from clearmd.frontend.ttk import art
from clearmd.frontend.ttk.brand import CARD, MUTED, PAGE, SOFT
from clearmd.frontend.ttk.layout import GAP, HALF, SPACE
from clearmd.i18n import Catalog


class ConvertView(ttk.Frame):
    """A card: "3 of 37", the current file with its icon, the bar, the time left; for a long file
    its timer and a reassurance. Cancel below."""

    def __init__(
        self, parent: tk.Misc, *, fonts: dict[str, tkfont.Font], on_cancel: Callable[[], None]
    ) -> None:
        super().__init__(parent, style=PAGE)
        self._catalog: Catalog | None = None
        self._icon: ImageTk.PhotoImage | None = None
        self._texts: list[tuple[Any, str]] = []

        card = ttk.Frame(self, style=CARD, padding=3 * SPACE)
        card.pack(fill="x")
        self.counter = ttk.Label(card, font=fonts["title"])
        self.counter.pack(anchor="w")
        now = ttk.Label(card, style=MUTED)
        now.pack(anchor="w", pady=(GAP, 0))
        self._label(now, "gui.progress.current")
        self.file = ttk.Label(card, font=fonts["strong"], compound="left")
        self.file.pack(anchor="w", pady=(HALF, 0))
        self.bar = ttk.Progressbar(card, orient="horizontal", mode="determinate", maximum=1.0)
        self.bar.pack(fill="x", pady=(GAP, 0))
        self.time_left = ttk.Label(card, style=MUTED)
        self.time_left.pack(anchor="w", pady=(SPACE, 0))
        self.long_file = ttk.Label(card, style=MUTED)
        self.long_file.pack(anchor="w", pady=(SPACE, 0))

        actions = ttk.Frame(self, style=PAGE)
        actions.pack(fill="x", pady=(GAP, 0))
        self.cancel = ttk.Button(actions, style=SOFT, command=on_cancel)
        self.cancel.pack(side="right")
        self._label(self.cancel, "gui.progress.cancel")

    def clear(self) -> None:
        for label in (self.counter, self.file, self.time_left, self.long_file):
            label.configure(text="", image="")
        self.bar.configure(value=0.0)

    def show(self, progress: ProgressView) -> None:
        self.counter.configure(text=progress.counter)
        self._icon = ImageTk.PhotoImage(art.icon(progress.icon), master=self)
        self.file.configure(text=f"  {progress.name}", image=self._icon)
        self.bar.configure(value=progress.fraction)
        self.time_left.configure(text=progress.time_left or "")
        if progress.elapsed and self._catalog is not None:
            elapsed = self._catalog.text("gui.progress.elapsed", clock=progress.elapsed)
            self.long_file.configure(text=f"{elapsed} · {progress.long_file or ''}".strip(" ·"))
        else:
            self.long_file.configure(text="")

    def apply_language(self, catalog: Catalog) -> None:
        self._catalog = catalog
        for widget, key in self._texts:
            widget.configure(text=catalog.text(key))

    def _label(self, widget: Any, key: str) -> None:
        self._texts.append((widget, key))
