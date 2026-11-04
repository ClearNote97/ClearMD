"""Step 2, Review: what happens to each file, before anything is written (AC-07, AC-08)."""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from typing import Any

from clearmd.frontend.presenter.models import PlanView, RowKind
from clearmd.frontend.ttk.brand import CARD, PAGE, Palette
from clearmd.frontend.ttk.components.file_list import Column, FileList, ListRow
from clearmd.frontend.ttk.components.stats import Stats
from clearmd.frontend.ttk.layout import GAP, SPACE
from clearmd.i18n import Catalog

KEEP, OVERWRITE = "keep", "overwrite"
_ATTENTION = frozenset({RowKind.SKIPPED, RowKind.MISSING})


class ReviewView(ttk.Frame):
    """The figures, the list (skipped files in the warning colour, with what to do), the question
    about existing results when the setting is "ask" (the actions are in the page's bar)."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        fonts: dict[str, tkfont.Font],
    ) -> None:
        super().__init__(parent, style=PAGE)
        self._asks = False
        self._plan_id = -1
        self._texts: list[tuple[Any, str]] = []
        self._catalog: Catalog | None = None

        self.stats = Stats(self, fonts=fonts)
        self.stats.pack(fill="x")

        self.files = FileList(
            self,
            name_heading="gui.main.column_name",
            columns=(Column("location", 220), Column("what", 320, stretch=True)),
            height=4,
            checks=False,  # a list to read: nothing on Review acts on a selection (014)
        )
        self.files.pack(fill="both", expand=True, pady=(GAP, 0))

        self.existing = ttk.Frame(self, style=CARD, padding=GAP)
        question = ttk.Label(self.existing, font=fonts["strong"])
        question.pack(anchor="w")
        self._label(question, "gui.plan.existing_question")
        self.decision = tk.StringVar(value=KEEP)
        answers = ttk.Frame(self.existing, style="TFrame")
        answers.pack(fill="x", pady=(SPACE, 0))
        self.keep = ttk.Radiobutton(answers, variable=self.decision, value=KEEP)
        self.keep.pack(side="left")
        self._label(self.keep, "gui.plan.keep")
        self.overwrite = ttk.Radiobutton(answers, variable=self.decision, value=OVERWRITE)
        self.overwrite.pack(side="left", padx=(GAP, 0))
        self._label(self.overwrite, "gui.plan.overwrite")

    def show(self, plan: PlanView) -> None:
        self.stats.show(plan.stats)
        # What will not be converted first: it is what the user may want to fix.
        rows = sorted(plan.rows, key=lambda row: row.kind not in _ATTENTION)
        self.files.show(
            [
                ListRow(row.icon, row.name, (row.location, row.detail),
                        tag="warning" if row.kind in _ATTENTION else "")
                for row in rows
            ]
        )  # fmt: skip
        same = plan.plan_id == self._plan_id  # the same plan shown again: the answer stays
        self._plan_id = plan.plan_id
        self._asks = plan.asks_about_existing
        if not same:
            self.decision.set(KEEP)
        self.existing.pack_forget()
        if self._asks:
            self.existing.pack(side="bottom", fill="x", pady=(GAP, 0), before=self.files)

    def forget(self) -> None:
        """The plan was dropped (an edit): nothing of it stays on screen (code review of 007);
        its cards wait, faded (014)."""
        self._wait()
        self.files.show([])
        self.existing.pack_forget()
        self._asks = False
        self._plan_id = -1

    def overwrite_answer(self) -> bool | None:
        """The answer about existing results, when the plan asks it (setting "ask")."""
        return self.decision.get() == OVERWRITE if self._asks else None

    def _wait(self) -> None:
        names = ("gui.plan.stat_convert", "gui.plan.stat_skipped", "gui.plan.stat_existing")
        catalog = self._catalog
        self.stats.waiting([catalog.text(name) for name in names] if catalog else [])

    def apply_language(self, catalog: Catalog) -> None:
        self._catalog = catalog
        if self.stats.dimmed or not self.stats.figures():
            self._wait()
        for widget, key in self._texts:
            widget.configure(text=catalog.text(key))
        self.files.apply_headings(
            catalog.text("gui.main.column_name"),
            [catalog.text("gui.main.column_location"), catalog.text("gui.plan.column_what")],
            catalog.text("gui.plan.nothing"),
        )

    def apply_palette(self, palette: Palette) -> None:
        self.stats.apply_palette(palette)
        self.files.apply_palette(palette)

    def _label(self, widget: Any, key: str) -> None:
        self._texts.append((widget, key))
