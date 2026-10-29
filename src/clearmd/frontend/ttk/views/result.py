"""Step 4, Results: the figures, each problem in plain words, Open results folder (AC-11, AC-12)."""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from typing import Any

from clearmd.frontend.presenter.models import ResultView
from clearmd.frontend.ttk.brand import CARD, ON_PAGE, PAGE, Palette
from clearmd.frontend.ttk.components.file_list import Column, FileList, ListRow
from clearmd.frontend.ttk.components.stats import Stats
from clearmd.frontend.ttk.layout import GAP, SPACE
from clearmd.i18n import Catalog


class ResultsView(ttk.Frame):
    """The figures; then either "every file was converted" or the list of what needs attention;
    Convert more and Open results folder."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        fonts: dict[str, tkfont.Font],
    ) -> None:
        super().__init__(parent, style=PAGE)
        self._texts: list[tuple[Any, str]] = []

        self.stats = Stats(self, fonts=fonts)
        self.stats.pack(fill="x")

        self.all_good = ttk.Frame(self, style=CARD, padding=3 * SPACE)
        message = ttk.Label(self.all_good, font=fonts["strong"], wraplength=640)
        message.pack(anchor="w")
        self._label(message, "gui.result.all_good")

        self.problems_title = ttk.Label(self, style=ON_PAGE, font=fonts["strong"])
        self._label(self.problems_title, "gui.result.problems")
        self.problems = FileList(
            self,
            name_heading="gui.main.column_name",
            columns=(Column("what", 520, stretch=True),),
            height=4,
        )
        # The selected problem in full: a long explanation does not fit its column.
        self.detail = ttk.Label(self, style=ON_PAGE, wraplength=760, justify="left")
        self.problems.tree.bind("<<TreeviewSelect>>", lambda _event: self._show_detail())

    def show(self, result: ResultView) -> None:
        tree = self.problems.tree
        selected = tree.index(tree.selection()[0]) if tree.selection() else 0
        keep = len(tree.get_children()) == len(result.rows)  # the same result again (settings)
        self.stats.show(result.stats)
        for widget in (self.all_good, self.problems_title, self.problems, self.detail):
            widget.pack_forget()
        if result.rows:
            self.problems_title.pack(anchor="w", pady=(GAP, 0))
            self.problems.pack(fill="both", expand=True, pady=(SPACE, 0))
            self.problems.show(
                [ListRow(row.icon, row.name, (row.detail,), tag="warning") for row in result.rows]
            )
            self.detail.pack(fill="x", pady=(SPACE, 0))
            children = tree.get_children()
            row = children[selected if keep and selected < len(children) else 0]
            tree.selection_set(row)
            tree.focus(row)
            self._show_detail()
        else:
            self.all_good.pack(fill="x", pady=(GAP, 0))

    def _show_detail(self) -> None:
        row = self.problems.current()
        self.detail.configure(text=f"{row.name}: {row.values[0]}" if row else "")

    def apply_language(self, catalog: Catalog) -> None:
        for widget, key in self._texts:
            widget.configure(text=catalog.text(key))
        self.problems.apply_headings(
            catalog.text("gui.main.column_name"),
            [catalog.text("gui.result.column_what")],
            "",
        )

    def apply_palette(self, palette: Palette) -> None:
        self.stats.apply_palette(palette)
        self.problems.apply_palette(palette)

    def _label(self, widget: Any, key: str) -> None:
        self._texts.append((widget, key))
