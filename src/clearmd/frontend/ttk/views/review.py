"""Step 2, Review: what happens to each file, before anything is written (AC-07, AC-08); under
the list, the selected row in full: why, what to do, and its whole folder (feature 035, AC-05)."""

import tkinter as tk
import tkinter.font as tkfont
from pathlib import PurePath
from tkinter import ttk
from typing import Any

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.presenter.models import PlanView, RowKind
from clearmd.frontend.ttk.components.file_list import Column, FileList, ListRow
from clearmd.frontend.ttk.components.flow_row import FlowRow
from clearmd.frontend.ttk.components.stats import Stats
from clearmd.frontend.ttk.visuals.style_names import CARD, ON_PAGE, PAGE
from clearmd.i18n import Catalog

KEEP, OVERWRITE, CHANGED = "keep", "overwrite", "changed"  # changed: feature 028
_ATTENTION = frozenset({RowKind.SKIPPED, RowKind.MISSING})
_FIRST = frozenset({RowKind.SKIPPED, RowKind.MISSING, RowKind.EXISTS})  # selected at first


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
            columns=(Column("location", 144), Column("what", 320, stretch=True)),
            height=4,
            checks=False,  # a list to read: nothing on Review acts on a selection (014)
            wrap=1,  # "What Happens" whole, on its lines (040)
            name_width=248,  # narrower names and folders: the reason gets the room
        )
        self.files.pack(fill="both", expand=True, pady=(GAP, 0))
        # The selected row in full: nothing cut without another way to read it (035, AC-05).
        self.detail = ttk.Label(self, style=ON_PAGE, justify="left")
        self.detail.bind(
            "<Configure>", lambda event: self.detail.configure(wraplength=max(event.width, 200))
        )
        self.files.tree.bind("<<TreeviewSelect>>", lambda _event: self._show_detail(), add="+")
        self._see: str | None = None
        self.files.tree.bind("<Map>", lambda _event: self.after_idle(self._see_first), add="+")

        self.existing = ttk.Frame(self, style=CARD, padding=GAP)
        question = ttk.Label(self.existing, font=fonts["strong"])
        question.pack(anchor="w")
        self._label(question, "gui.plan.existing_question")
        self.decision = tk.StringVar(value=KEEP)
        # The answers on one row, or one per row when they do not fit (Spanish, 028).
        answers = FlowRow(self.existing)
        answers.pack(fill="x", pady=(SPACE, 0))
        self.answers = answers
        self.keep = ttk.Radiobutton(answers, variable=self.decision, value=KEEP)
        self._label(self.keep, "gui.plan.keep")
        self.overwrite = ttk.Radiobutton(answers, variable=self.decision, value=OVERWRITE)
        self._label(self.overwrite, "gui.plan.overwrite")
        self.changed = ttk.Radiobutton(answers, variable=self.decision, value=CHANGED)
        self._label(self.changed, "gui.plan.changed")
        for answer in (self.keep, self.overwrite, self.changed):
            answers.add(answer)

    def show(self, plan: PlanView) -> None:
        self.stats.show(plan.stats)
        # What will not be converted first: it is what the user may want to fix.
        rows = sorted(plan.rows, key=lambda row: row.kind not in _ATTENTION)
        self.files.show(
            [
                ListRow(row.icon, row.name, (_last_folder(row.location), row.detail),
                        tag="warning" if row.kind in _ATTENTION else "", payload=row)
                for row in rows
            ]
        )  # fmt: skip
        same = plan.plan_id == self._plan_id  # the same plan shown again: the answer stays
        self._plan_id = plan.plan_id
        self._asks = plan.asks_about_existing
        if not same:
            self.decision.set(KEEP)
        self.existing.pack_forget()
        self.detail.pack_forget()
        if self._asks:
            self.existing.pack(side="bottom", fill="x", pady=(GAP, 0), before=self.files)
        if rows:  # under the list, above the question
            self.detail.pack(side="bottom", fill="x", pady=(SPACE, 0), before=self.files)
            first = next((i for i, row in enumerate(rows) if row.kind in _FIRST), 0)
            if not same or not self.files.tree.selection():
                item = self.files.tree.get_children()[first]
                self.files.tree.selection_set(item)
                self.files.tree.focus(item)
                self._see = item  # once the list is on screen: hidden, it has no rows to show
                if self.files.tree.winfo_ismapped():
                    self.after_idle(self._see_first)  # once the detail and question are laid out
        self._show_detail()

    def forget(self) -> None:
        """The plan was dropped (an edit): nothing of it stays on screen (code review of 007);
        its cards wait, faded (014)."""
        self._wait()
        self.files.show([])
        self.existing.pack_forget()
        self.detail.pack_forget()
        self._asks = False
        self._plan_id = -1

    def _see_first(self) -> None:
        """Show the row selected at first: from the top, so rows above it are not hidden."""
        if self._see is not None and self.files.tree.exists(self._see):
            self.files.tree.yview_moveto(0)
            self.files.tree.see(self._see)
        self._see = None

    def _show_detail(self) -> None:
        current = self.files.current()
        row = current.payload if current is not None else None
        if row is None or self._catalog is None:
            self.detail.configure(text="")
            return
        folder = self._catalog.text("gui.main.column_location")
        self.detail.configure(text=f"{row.name}: {row.detail}\n{folder}: {row.location}")

    def overwrite_answer(self) -> bool | str | None:
        """The answer about existing results, when the plan asks it (setting "ask"): replace
        them (True), keep them (False), or replace those whose original changed ("changed")."""
        if not self._asks:
            return None
        answer = self.decision.get()
        return "changed" if answer == CHANGED else answer == OVERWRITE

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
        self.answers.refresh()
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


def _last_folder(location: str) -> str:
    """The list's folder column: the last folder's name (the whole path is in the detail)."""
    return PurePath(location).name or location
