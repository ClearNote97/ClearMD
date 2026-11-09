"""Step 3, Convert: what is ready before the batch, then the progress (AC-09)."""

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.presenter.models import ProgressView
from clearmd.frontend.pyside.components.primitives import card, label, restyle
from clearmd.frontend.pyside.layout.units import ICON
from clearmd.frontend.pyside.visuals.images import icon
from clearmd.i18n import Catalog


class ConvertView(QWidget):
    """Before the batch, a card says what is ready and where it goes; then "3 of 37", the
    current file with its icon, the bar, the time left, and for a long file its timer."""

    def __init__(self) -> None:
        super().__init__()
        self._texts: list[tuple[QLabel | QPushButton | QRadioButton, str]] = []
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(GAP)
        self._catalog: Catalog | None = None
        self.ready, ready_layout = card(padding=3 * SPACE)
        self.ready_count = label("bigText", wrap=True)
        # What happens to the results that already exist, as decided (035, AC-08).
        self.ready_existing = label("onPage", wrap=True)
        self.ready_existing.hide()
        self.ready_where = label("muted", wrap=True)
        for widget in (self.ready_count, self.ready_existing, self.ready_where):
            ready_layout.addWidget(widget)
        self.layout_.addWidget(self.ready)
        self.progress_card, progress = card(padding=3 * SPACE)
        self.counter = label("bigText")
        progress.addWidget(self.counter)
        progress.addSpacing(SPACE)
        now = label("muted")
        self._text(now, "gui.progress.current")
        progress.addWidget(now)
        current = QHBoxLayout()
        current.setSpacing(SPACE)
        self.file_icon = QLabel()
        self.file = label("strong")
        current.addWidget(self.file_icon)
        current.addWidget(self.file, 1)
        progress.addLayout(current)
        progress.addSpacing(SPACE)
        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        self.bar.setTextVisible(False)
        progress.addWidget(self.bar)
        self.time_left = label("muted")
        self.long_file = label("muted", wrap=True)
        progress.addWidget(self.time_left)
        progress.addWidget(self.long_file)
        self.layout_.addWidget(self.progress_card)
        self.progress_card.hide()
        self.layout_.addStretch(1)
        self.dimmed = False
        self._fade(True)

    def show_ready(self, count: str, where: str) -> None:
        self.progress_card.hide()
        self._fade(False)
        first, _, rest = count.partition("\n")  # how many, then the existing results' fate
        self.ready_count.setText(first)
        self.ready_existing.setText(rest)
        self.ready_existing.setVisible(bool(rest))
        self.ready_where.setText(where)
        self.ready.show()

    def forget(self, where: str = "") -> None:
        self.progress_card.hide()
        self._fade(True)
        catalog = self._catalog
        self.ready_count.setText(catalog.text("gui.convert.ready", count="—") if catalog else "—")
        self.ready_existing.hide()
        self.ready_where.setText(where)
        self.ready.show()

    def clear(self) -> None:
        """The batch starts: the progress replaces the ready card."""
        self.ready.hide()
        self.progress_card.show()
        for widget in (self.counter, self.file, self.time_left, self.long_file):
            widget.setText("")
        self.file_icon.clear()
        self.bar.setValue(0)

    def show(self, progress: ProgressView) -> None:  # type: ignore[override]  # the presenter's
        self.counter.setText(progress.counter)
        self.file_icon.setPixmap(icon(progress.icon).pixmap(ICON, ICON))
        self.file.setText(progress.name)
        self.bar.setValue(round(progress.fraction * 1000))
        self.time_left.setText(progress.time_left or "")
        if progress.elapsed and self._catalog is not None:
            elapsed = self._catalog.text("gui.progress.elapsed", clock=progress.elapsed)
            self.long_file.setText(f"{elapsed} · {progress.long_file or ''}".strip(" ·"))
        else:
            self.long_file.setText("")

    def _fade(self, dimmed: bool) -> None:
        self.dimmed = dimmed
        restyle(self.ready, "dim", "true" if dimmed else "false")

    def apply_language(self, catalog: Catalog) -> None:
        for widget, key in self._texts:
            widget.setText(catalog.text(key))
        self._catalog = catalog
        if self.dimmed:
            self.ready_count.setText(catalog.text("gui.convert.ready", count="—"))

    def _text(self, widget: QLabel | QPushButton | QRadioButton, key: str) -> None:
        self._texts.append((widget, key))
