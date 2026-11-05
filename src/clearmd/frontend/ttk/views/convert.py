"""Step 3, Convert: where it is, the time left, and Cancel always at hand (UX §2; AC-09, AC-10)."""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from typing import Any

from PIL import ImageTk

from clearmd.frontend.design.metrics import GAP, HALF, SPACE
from clearmd.frontend.presenter.models import ProgressView
from clearmd.frontend.ttk.visuals import marks
from clearmd.frontend.ttk.visuals.style_names import CARD, DIM, DIM_CARD, MUTED, PAGE
from clearmd.i18n import Catalog


class ConvertView(ttk.Frame):
    """A card: "3 of 37", the current file with its icon, the bar, the time left; for a long file
    its timer and a reassurance. Before it starts, a card says what is ready and where it goes."""

    def __init__(self, parent: tk.Misc, *, fonts: dict[str, tkfont.Font]) -> None:
        super().__init__(parent, style=PAGE)
        self._catalog: Catalog | None = None
        self._icon: ImageTk.PhotoImage | None = None
        self._texts: list[tuple[Any, str]] = []

        # Before the batch: what is ready and where it goes; then the progress (ADR-0029).
        self.ready = ttk.Frame(self, style=CARD, padding=3 * SPACE)
        self.ready_count = ttk.Label(self.ready, font=fonts["title"])
        self.ready_count.pack(anchor="w")
        self.ready_where = ttk.Label(self.ready, style=MUTED, wraplength=640, justify="left")
        self.ready_where.pack(anchor="w", pady=(SPACE, 0))
        self.ready.pack(fill="x")
        self.dimmed = False
        self._fade(True)  # nothing chosen yet: it waits, faded (014)

        card = ttk.Frame(self, style=CARD, padding=3 * SPACE)
        self.progress_card = card
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

    def show_ready(self, count: str, where: str) -> None:
        """The batch has not started: what is ready, and where the results go."""
        self.progress_card.pack_forget()
        self._fade(False)
        self.ready_count.configure(text=count)
        self.ready_where.configure(text=where)
        self.ready.pack(fill="x")

    def forget(self, where: str = "") -> None:
        """No plan any more: neither what was ready nor an old progress stays on screen; the
        ready card waits, faded, with nothing counted (014)."""
        self.progress_card.pack_forget()
        self._fade(True)
        ready = self._catalog.text("gui.convert.ready", count="—") if self._catalog else "—"
        self.ready_count.configure(text=ready)
        self.ready_where.configure(text=where)
        self.ready.pack(fill="x")

    def _fade(self, dimmed: bool) -> None:
        self.dimmed = dimmed
        self.ready.configure(style=DIM_CARD if dimmed else CARD)
        self.ready_count.configure(style=DIM if dimmed else "TLabel")
        self.ready_where.configure(style=DIM if dimmed else MUTED)

    def clear(self) -> None:
        """The batch starts: the progress replaces the ready card."""
        self.ready.pack_forget()
        self.progress_card.pack(fill="x")
        for label in (self.counter, self.file, self.time_left, self.long_file):
            label.configure(text="", image="")
        self.bar.configure(value=0.0)

    def show(self, progress: ProgressView) -> None:
        self.counter.configure(text=progress.counter)
        self._icon = ImageTk.PhotoImage(marks.icon(progress.icon), master=self)
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
        if self.dimmed:
            self.ready_count.configure(text=catalog.text("gui.convert.ready", count="—"))
        for widget, key in self._texts:
            widget.configure(text=catalog.text(key))

    def _label(self, widget: Any, key: str) -> None:
        self._texts.append((widget, key))
