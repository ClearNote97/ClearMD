"""The figures: one card per figure, side by side, the figure in its tone and its label below."""

from collections.abc import Sequence

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from clearmd.frontend.design.metrics import GAP, HALF
from clearmd.frontend.presenter.models import Stat
from clearmd.frontend.pyside.components.primitives import card, label


class Stats(QWidget):
    """One card per figure, side by side; the figure in its tone, its label below. Before there is
    anything to count, the cards wait faded with "—" (feature 014)."""

    def __init__(self) -> None:
        super().__init__()
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(GAP)
        self._cards: list[tuple[QLabel, QLabel]] = []
        self.dimmed = False

    def show_stats(self, stats: Sequence[Stat]) -> None:
        self._fill([(str(stat.value), stat.label, stat.tone.value) for stat in stats], dim=False)

    def waiting(self, labels: Sequence[str]) -> None:
        self._fill([("—", name, "neutral") for name in labels], dim=True)

    def figures(self) -> list[tuple[str, str]]:
        """The figures as shown (for tests): (label, figure)."""
        return [(name.text(), figure.text()) for figure, name in self._cards]

    def tones(self) -> list[str]:
        """The figures' tones as drawn (for tests)."""
        return [str(figure.property("tone")) for figure, _ in self._cards]

    def _fill(self, cards: Sequence[tuple[str, str, str]], *, dim: bool) -> None:
        while self._layout.count():
            child = self._layout.takeAt(0)
            widget = child.widget() if child is not None else None
            if widget is not None:
                widget.deleteLater()
        self._cards.clear()
        self.dimmed = dim
        for figure_text, name_text, tone in cards:
            frame, layout = card()
            frame.setProperty("dim", "true" if dim else "false")
            layout.setSpacing(HALF)
            figure = label("figure", figure_text)
            figure.setProperty("tone", "neutral" if dim else tone)
            name = label("muted", name_text)
            layout.addWidget(figure)
            layout.addWidget(name)
            self._layout.addWidget(frame, 1)
            self._cards.append((figure, name))
