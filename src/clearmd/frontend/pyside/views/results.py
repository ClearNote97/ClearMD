"""Step 4, Results: the figures, where the results are (as text to read and copy, feature 035),
and what needs attention, each row in its own tone (AC-11; 035 AC-03, AC-06)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QRadioButton, QVBoxLayout, QWidget

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.presenter.models import ResultView, Tone
from clearmd.frontend.pyside.components.file_list import FileList, ListRow
from clearmd.frontend.pyside.components.primitives import card, label
from clearmd.frontend.pyside.components.stats import Stats
from clearmd.i18n import Catalog


class ResultsView(QWidget):
    """The figures; then "every file was converted", or what needs attention with the selected
    problem in full below the list."""

    def __init__(self) -> None:
        super().__init__()
        self._texts: list[tuple[QLabel | QPushButton | QRadioButton, str]] = []
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(GAP)
        self._catalog: Catalog | None = None
        self.stats = Stats()
        self.layout_.addWidget(self.stats)
        self.where = label("onPage", wrap=True)  # where the files are: selectable, copyable
        self.where.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.where.hide()
        self.layout_.addWidget(self.where)
        self.with_ai = label("muted", wrap=True)  # what to do with the result (audit v3, F4-06)
        self.with_ai.hide()
        self.layout_.addWidget(self.with_ai)
        self.all_good, good_layout = card(padding=3 * SPACE)
        message = label("strong", wrap=True)
        self._text(message, "gui.result.all_good")
        good_layout.addWidget(message)
        self.layout_.addWidget(self.all_good)
        self.problems_title = label("strong")
        self._text(self.problems_title, "gui.result.problems")
        self.layout_.addWidget(self.problems_title)
        self.problems = FileList(1, widths=(240,))
        self.layout_.addWidget(self.problems, 1)
        self.detail = label("onPage", wrap=True)
        self.layout_.addWidget(self.detail)
        self.problems.selection_changed.connect(self._show_detail)
        self._filler = QWidget()
        self.layout_.addWidget(self._filler, 1)
        self._showing(None)

    def show(self, result: ResultView) -> None:  # type: ignore[override]  # the presenter's
        current = self.problems.current()
        rows = self.problems.rows()
        # Never a row chosen for the user (audit v3, F3-03); the same result again keeps theirs.
        selected = rows.index(current) if current in rows else -1
        keep = len(rows) == len(result.rows)
        self.stats.show_stats(result.stats)
        self.where.setText(result.where)
        self.where.setVisible(bool(result.where))
        self.with_ai.setText(result.with_ai)
        self.with_ai.setVisible(bool(result.with_ai))
        if result.rows:
            self.problems.show_rows(
                [
                    ListRow(
                        row.icon,
                        row.name,
                        (row.detail,),
                        warning=row.tone is Tone.WARNING,  # NEUTRAL: informative, plain
                        danger=row.tone is Tone.DANGER,
                    )
                    for row in result.rows
                ]
            )
            self._showing(True)
            if keep and 0 <= selected < len(result.rows):
                self.problems.select(selected)
            self._show_detail()
        else:
            self._showing(False)

    def forget(self) -> None:
        self._wait()
        self.problems.show_rows([])
        self.where.setText("")
        self.where.hide()
        self.with_ai.setText("")
        self.with_ai.hide()
        self._showing(None)

    def _showing(self, problems: bool | None) -> None:
        """``None``: nothing yet; ``False``: all good; ``True``: the problems."""
        self.all_good.setVisible(problems is False)
        for widget in (self.problems_title, self.problems, self.detail):
            widget.setVisible(problems is True)
        self._filler.setVisible(problems is not True)

    def _show_detail(self) -> None:
        row = self.problems.current()
        self.detail.setText(f"{row.name}: {row.values[0]}" if row else "")

    def _wait(self) -> None:
        names = ("gui.result.stat_converted", "gui.result.stat_skipped", "gui.result.stat_failed")
        catalog = self._catalog
        self.stats.waiting([catalog.text(name) for name in names] if catalog else [])

    def apply_language(self, catalog: Catalog) -> None:
        for widget, key in self._texts:
            widget.setText(catalog.text(key))
        self._catalog = catalog
        if self.stats.dimmed or not self.stats.figures():
            self._wait()
        self.problems.apply_headings(
            [catalog.text("gui.main.column_name"), catalog.text("gui.result.column_what")], ""
        )

    def apply_palette(self, palette: Palette) -> None:
        self.problems.apply_palette(palette)

    def _text(self, widget: QLabel | QPushButton | QRadioButton, key: str) -> None:
        self._texts.append((widget, key))
