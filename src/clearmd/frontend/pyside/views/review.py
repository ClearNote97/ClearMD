"""Step 2, Review: what happens to each file, before anything is written (AC-07, AC-08)."""

from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from clearmd.frontend.design.metrics import GAP
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.presenter.models import PlanView, RowKind
from clearmd.frontend.pyside.components.file_list import FileList, ListRow
from clearmd.frontend.pyside.components.primitives import card, label, radio_button
from clearmd.frontend.pyside.components.stats import Stats
from clearmd.i18n import Catalog

_ATTENTION = frozenset({RowKind.SKIPPED, RowKind.MISSING})


class ReviewView(QWidget):
    """The figures, the list (what will not be converted first, in the warning colour, with what
    to do), and the question about existing results when the setting is "ask"."""

    def __init__(self) -> None:
        super().__init__()
        self._texts: list[tuple[QLabel | QPushButton | QRadioButton, str]] = []
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(GAP)
        self._catalog: Catalog | None = None
        self._asks = False
        self._plan_id = -1
        self.stats = Stats()
        self.layout_.addWidget(self.stats)
        self.files = FileList(2, widths=(240, 220))
        self.layout_.addWidget(self.files, 1)
        self.existing, existing_layout = card()
        question = label("strong")
        self._text(question, "gui.plan.existing_question")
        existing_layout.addWidget(question)
        answers = QHBoxLayout()
        self._answers = QButtonGroup(self)
        self.keep = radio_button(self._answers)
        self.overwrite = radio_button(self._answers)
        self._text(self.keep, "gui.plan.keep")
        self._text(self.overwrite, "gui.plan.overwrite")
        answers.addWidget(self.keep)
        answers.addSpacing(GAP)
        answers.addWidget(self.overwrite)
        answers.addStretch(1)
        existing_layout.addLayout(answers)
        self.keep.setChecked(True)
        self.layout_.addWidget(self.existing)
        self.existing.hide()

    def show(self, plan: PlanView) -> None:  # type: ignore[override]  # the presenter's, not QWidget's
        self.stats.show_stats(plan.stats)
        rows = sorted(plan.rows, key=lambda row: row.kind not in _ATTENTION)
        self.files.show_rows(
            [
                ListRow(row.icon, row.name, (row.location, row.detail),
                        warning=row.kind in _ATTENTION)
                for row in rows
            ]
        )  # fmt: skip
        if plan.plan_id != self._plan_id:  # another plan: the answer starts over
            self.keep.setChecked(True)
        self._plan_id = plan.plan_id
        self._asks = plan.asks_about_existing
        self.existing.setVisible(self._asks)

    def forget(self) -> None:
        self._wait()
        self.files.show_rows([])
        self.existing.hide()
        self._asks = False
        self._plan_id = -1

    def overwrite_answer(self) -> bool | None:
        return self.overwrite.isChecked() if self._asks else None

    def _wait(self) -> None:
        names = ("gui.plan.stat_convert", "gui.plan.stat_skipped", "gui.plan.stat_existing")
        catalog = self._catalog
        self.stats.waiting([catalog.text(name) for name in names] if catalog else [])

    def apply_language(self, catalog: Catalog) -> None:
        for widget, key in self._texts:
            widget.setText(catalog.text(key))
        self._catalog = catalog
        if self.stats.dimmed or not self.stats.figures():
            self._wait()
        self.files.apply_headings(
            [
                catalog.text("gui.main.column_name"),
                catalog.text("gui.main.column_location"),
                catalog.text("gui.plan.column_what"),
            ],
            catalog.text("gui.plan.nothing"),
        )

    def apply_palette(self, palette: Palette) -> None:
        self.files.apply_palette(palette)

    def _text(self, widget: QLabel | QPushButton | QRadioButton, key: str) -> None:
        self._texts.append((widget, key))
