"""Step 4, Results: the figures, where the files are (selectable text, feature 035), and what
needs attention, each row in its tone (AC-11)."""

import flet as ft

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.flet.components.file_list import FileList, ListRow
from clearmd.frontend.flet.components.primitives import Wording, card, label
from clearmd.frontend.flet.components.stats import Stats
from clearmd.frontend.presenter.models import ResultView, Tone
from clearmd.i18n import Catalog

_TONES = {Tone.DANGER: "danger", Tone.WARNING: "warning"}  # a row's tone, as a colour role


class ResultsView:
    """The figures; then "every file was converted", or what needs attention with the selected
    problem in full below the list."""

    def __init__(self) -> None:
        self._wording = Wording()
        self._catalog: Catalog | None = None
        self.stats = Stats()
        # Where the files are: text to read and copy, always shown when there is a place (035).
        self.where = label("onPage")
        self.where.selectable = True
        self.where.visible = False
        message = label("strong")
        self._wording.add(message, "gui.result.all_good")
        self.all_good = card([message], padding=3 * SPACE)
        self.problems_title = label("strong")
        self._wording.add(self.problems_title, "gui.result.problems")
        self.problems = FileList(1, widths=(240,), on_selection=self._show_detail)
        self.detail = label("onPage")
        self.control = ft.Column(
            [self.stats.control, self.where, self.all_good, self.problems_title,
             self.problems.control, self.detail],
            spacing=GAP,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,  # full-width cards, as in Qt
        )  # fmt: skip
        self._showing(None)

    def show(self, result: ResultView) -> None:
        current = self.problems.current()
        rows = self.problems.rows()
        selected = rows.index(current) if current in rows else 0
        keep = len(rows) == len(result.rows)  # the same result again (settings)
        self.stats.show_stats(result.stats)
        self.where.value = result.where
        self.where.visible = bool(result.where)
        if result.rows:
            self.problems.show_rows(
                [ListRow(row.icon, row.name, (row.detail,), tone=_TONES.get(row.tone, "warning"))
                 for row in result.rows]
            )  # fmt: skip
            self._showing(True)
            self.problems.select(selected if keep and selected < len(result.rows) else 0)
        else:
            self._showing(False)

    def forget(self) -> None:
        self._wait()
        self.problems.show_rows([])
        self.where.value, self.where.visible = "", False
        self._showing(None)

    def _showing(self, problems: bool | None) -> None:
        """``None``: nothing yet; ``False``: all good; ``True``: the problems."""
        self.all_good.visible = problems is False
        for control in (self.problems_title, self.problems.control, self.detail):
            control.visible = problems is True

    def _show_detail(self) -> None:
        row = self.problems.current()
        self.detail.value = f"{row.name}: {row.values[0]}" if row else ""

    def _wait(self) -> None:
        names = ("gui.result.stat_converted", "gui.result.stat_skipped", "gui.result.stat_failed")
        catalog = self._catalog
        self.stats.waiting([catalog.text(name) for name in names] if catalog else [])

    def apply_language(self, catalog: Catalog) -> None:
        self._wording.apply(catalog)
        self._catalog = catalog
        if self.stats.dimmed or not self.stats.figures():
            self._wait()
        self.problems.apply_headings(
            [catalog.text("gui.main.column_name"), catalog.text("gui.result.column_what")], ""
        )
