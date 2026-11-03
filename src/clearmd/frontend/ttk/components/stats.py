"""A row of figures in cards (ADR-0027): "To convert 12 · Skipped 2 · Already exist 1"."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Sequence
from tkinter import ttk

from clearmd.frontend.presenter.models import Stat, Tone
from clearmd.frontend.ttk.brand import CARD, DIM, DIM_CARD, MUTED, PAGE, Palette
from clearmd.frontend.ttk.layout import GAP, HALF


class Stats(ttk.Frame):
    """One card per figure, side by side; the figure in its tone, its label below."""

    def __init__(self, parent: tk.Misc, *, fonts: dict[str, tkfont.Font]) -> None:
        super().__init__(parent, style=PAGE)
        self._fonts = fonts
        self._palette: Palette | None = None
        self._stats: tuple[Stat, ...] = ()
        self._waiting: tuple[str, ...] = ()  # the figures' names, faded, before there are any
        self._cards: list[tuple[ttk.Label, ttk.Label]] = []
        self.dimmed = False

    def apply_palette(self, palette: Palette) -> None:
        self._palette = palette
        if self.dimmed:
            self.waiting(self._waiting)
        else:
            self.show(self._stats)

    def waiting(self, labels: Sequence[str]) -> None:
        """The cards before there is anything to count: faded, "—" for each figure (014)."""
        self.show(())
        self._waiting = tuple(labels)
        self.dimmed = True
        for index, name in enumerate(self._waiting):
            card = ttk.Frame(self, style=DIM_CARD, padding=GAP)
            card.pack(side="left", fill="x", expand=True, padx=(0 if index == 0 else GAP, 0))
            figure = ttk.Label(card, text="—", style=DIM, font=self._fonts["title"])
            figure.pack(anchor="w")
            label = ttk.Label(card, text=name, style=DIM)
            label.pack(anchor="w", pady=(HALF, 0))
            self._cards.append((figure, label))

    def show(self, stats: Sequence[Stat]) -> None:
        self._stats = tuple(stats)
        self.dimmed = False
        for child in self.winfo_children():
            child.destroy()
        self._cards.clear()
        for index, stat in enumerate(self._stats):
            card = ttk.Frame(self, style=CARD, padding=GAP)
            card.pack(side="left", fill="x", expand=True, padx=(0 if index == 0 else GAP, 0))
            figure = ttk.Label(card, text=str(stat.value), font=self._fonts["title"])
            figure.pack(anchor="w")
            if self._palette is not None:
                figure.configure(foreground=self._colour(stat.tone, self._palette))
            label = ttk.Label(card, text=stat.label, style=MUTED)
            label.pack(anchor="w", pady=(HALF, 0))
            self._cards.append((figure, label))

    def figures(self) -> list[tuple[str, str]]:
        """The figures as shown (for tests)."""
        return [(label.cget("text"), figure.cget("text")) for figure, label in self._cards]

    @staticmethod
    def _colour(tone: Tone, palette: Palette) -> str:
        return {
            Tone.ACCENT: palette.accent_text,
            Tone.WARNING: palette.warning,
            Tone.DANGER: palette.danger,
            Tone.NEUTRAL: palette.text,
        }[tone]
