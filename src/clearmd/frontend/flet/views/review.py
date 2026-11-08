"""Step 2, Review: what happens to each file, before anything is written (AC-07, AC-08)."""

import flet as ft

from clearmd.frontend.design.metrics import GAP
from clearmd.frontend.flet.components.file_list import FileList, ListRow
from clearmd.frontend.flet.components.primitives import Choice, Wording, card, label
from clearmd.frontend.flet.components.stats import Stats
from clearmd.frontend.presenter.models import PlanView, RowKind
from clearmd.i18n import Catalog

_ATTENTION = frozenset({RowKind.SKIPPED, RowKind.MISSING})


class ReviewView:
    """The figures, the list (what will not be converted first, in the warning colour, with what
    to do), and the question about existing results when the setting is "ask"."""

    def __init__(self) -> None:
        self._wording = Wording()
        self._catalog: Catalog | None = None
        self._asks = False
        self._plan_id = -1
        self.stats = Stats()
        self.files = FileList(2, widths=(240, 220))
        question = label("strong")
        self._wording.add(question, "gui.plan.existing_question")
        self.answer = Choice(("keep", "overwrite", "changed"))  # changed: feature 028
        self._wording.add(self.answer.radios["keep"], "gui.plan.keep")
        self._wording.add(self.answer.radios["overwrite"], "gui.plan.overwrite")
        self._wording.add(self.answer.radios["changed"], "gui.plan.changed")
        self.existing = card([question, self.answer.control])
        self.existing.visible = False
        self.control = ft.Column(
            [self.stats.control, self.files.control, self.existing],
            spacing=GAP,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,  # full-width cards, as in Qt
        )

    def show(self, plan: PlanView) -> None:
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
            self.answer.set("keep")
        self._plan_id = plan.plan_id
        self._asks = plan.asks_about_existing
        self.existing.visible = self._asks

    def forget(self) -> None:
        self._wait()
        self.files.show_rows([])
        self.existing.visible = False
        self._asks = False
        self._plan_id = -1

    def overwrite_answer(self) -> bool | str | None:
        """Keep: False; Replace: True; only if the original changed: "changed" (028). ``None``:
        not asked, the setting decides."""
        if not self._asks:
            return None
        return "changed" if self.answer.value == "changed" else self.answer.value == "overwrite"

    def _wait(self) -> None:
        names = ("gui.plan.stat_convert", "gui.plan.stat_skipped", "gui.plan.stat_existing")
        catalog = self._catalog
        self.stats.waiting([catalog.text(name) for name in names] if catalog else [])

    def apply_language(self, catalog: Catalog) -> None:
        self._wording.apply(catalog)
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
