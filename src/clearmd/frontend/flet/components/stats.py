"""The figures: one card per figure, side by side, the figure in its tone and its label below."""

from collections.abc import Sequence

import flet as ft

from clearmd.frontend.design.metrics import GAP, HALF
from clearmd.frontend.flet.components.primitives import card, label
from clearmd.frontend.flet.visuals.look import TONES
from clearmd.frontend.flet.visuals.theme import role
from clearmd.frontend.presenter.models import Stat


class Stats:
    """One card per figure, side by side; the figure in its tone, its label below. Before there is
    anything to count, the cards wait faded with "—" (feature 014)."""

    def __init__(self) -> None:
        self.control = ft.Row(spacing=GAP)
        self._cards: list[tuple[ft.Text, ft.Text]] = []
        self.dimmed = False

    def show_stats(self, stats: Sequence[Stat]) -> None:
        self._fill([(str(stat.value), stat.label, stat.tone.value) for stat in stats], dim=False)

    def waiting(self, labels: Sequence[str]) -> None:
        self._fill([("—", name, "neutral") for name in labels], dim=True)

    def figures(self) -> list[tuple[str, str]]:
        """The figures as shown (for tests): (label, figure)."""
        return [(str(name.value), str(figure.value)) for figure, name in self._cards]

    def _fill(self, cards: Sequence[tuple[str, str, str]], *, dim: bool) -> None:
        self._cards.clear()
        self.dimmed = dim
        frames: list[ft.Control] = []
        for figure_text, name_text, tone in cards:
            figure = label("figure", figure_text)
            figure.color = role("dim_text" if dim else TONES.get(tone, "text"))
            name = label("muted", name_text)
            if dim:
                name.color = role("dim_text")
            frame = card([figure, name], spacing=HALF)
            frame.expand = 1
            if dim:
                frame.bgcolor = role("dim_card")
                frame.border = ft.Border.all(1, role("dim_card"))
            frames.append(frame)
            self._cards.append((figure, name))
        self.control.controls = frames
