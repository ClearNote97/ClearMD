"""Step 2, Review: what happens to each file, before anything is written (AC-07, AC-08)."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from tkinter import ttk
from typing import Any

from clearmd.frontend.presenter.models import PlanView, RowKind
from clearmd.frontend.ttk.brand import CARD, PAGE, PRIMARY, SOFT, Palette
from clearmd.frontend.ttk.components.file_list import Column, FileList, ListRow
from clearmd.frontend.ttk.components.stats import Stats
from clearmd.frontend.ttk.layout import GAP, SPACE
from clearmd.i18n import Catalog

KEEP, OVERWRITE = "keep", "overwrite"
_ATTENTION = frozenset({RowKind.SKIPPED, RowKind.MISSING})


class ReviewView(ttk.Frame):
    """The figures, the list (skipped files in the warning colour, with what to do), the question
    about existing results when the setting is "ask", Back and Convert."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        fonts: dict[str, tkfont.Font],
        on_back: Callable[[], None],
        on_confirm: Callable[[bool | None], None],
    ) -> None:
        super().__init__(parent, style=PAGE)
        self._on_confirm = on_confirm
        self._asks = False
        self._texts: list[tuple[Any, str]] = []

        self.stats = Stats(self, fonts=fonts)
        self.stats.pack(fill="x")

        self.files = FileList(
            self,
            name_heading="gui.main.column_name",
            columns=(Column("location", 220), Column("what", 320, stretch=True)),
            height=4,
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

        actions = ttk.Frame(self, style=PAGE)
        actions.pack(side="bottom", fill="x", pady=(GAP, 0))
        self.confirm = ttk.Button(actions, style=PRIMARY, command=self._confirm)
        self.confirm.pack(side="right")
        self._label(self.confirm, "gui.plan.confirm")
        self.back = ttk.Button(actions, style=SOFT, command=on_back)
        self.back.pack(side="right", padx=(0, SPACE))
        self._label(self.back, "gui.plan.back")
        self._actions = actions

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
        self._asks = plan.asks_about_existing
        self.decision.set(KEEP)
        self.existing.pack_forget()
        if self._asks:
            self.existing.pack(fill="x", pady=(GAP, 0), before=self._actions)

    def _confirm(self) -> None:
        self._on_confirm(self.decision.get() == OVERWRITE if self._asks else None)

    def apply_language(self, catalog: Catalog) -> None:
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
