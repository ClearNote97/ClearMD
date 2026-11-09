"""Step 4, Results: the figures, where the files are (text to read and copy, 035), each problem in
plain words with its tone, Open results folder (AC-11, AC-12)."""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from typing import Any

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.presenter.models import ResultView, Tone
from clearmd.frontend.ttk.components.file_list import Column, FileList, ListRow
from clearmd.frontend.ttk.components.stats import Stats
from clearmd.frontend.ttk.components.where_text import WhereText
from clearmd.frontend.ttk.visuals.style_names import CARD, ON_PAGE, PAGE
from clearmd.i18n import Catalog

_TAGS = {Tone.DANGER: "danger", Tone.WARNING: "warning"}  # a row's tone, its colour (AC-03)


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
        self._catalog: Catalog | None = None

        self.stats = Stats(self, fonts=fonts)
        self.stats.pack(fill="x")
        self.where = WhereText(self, fonts=fonts)  # where the files are (feature 035, AC-06)

        self.all_good = ttk.Frame(self, style=CARD, padding=3 * SPACE)
        self.all_good_text = ttk.Label(self.all_good, font=fonts["strong"], wraplength=640)
        self.all_good_text.pack(anchor="w")
        self._headline = ""  # in place of "every file was converted" when nothing was (038)

        self.problems_title = ttk.Label(self, style=ON_PAGE, font=fonts["strong"])
        self._label(self.problems_title, "gui.result.problems")
        self.problems = FileList(
            self,
            name_heading="gui.main.column_name",
            columns=(Column("what", 520, stretch=True),),
            height=4,
            checks=False,  # a list to read: a row chosen shows its detail, nothing more (014)
        )
        # The selected problem in full: a long explanation does not fit its column.
        self.detail = ttk.Label(self, style=ON_PAGE, wraplength=760, justify="left")
        self.detail.bind(  # as wide as the page: a long text never runs past it (007, A7-4)
            "<Configure>", lambda event: self.detail.configure(wraplength=max(event.width, 200))
        )
        self.problems.tree.bind("<<TreeviewSelect>>", lambda _event: self._show_detail())

    def show(self, result: ResultView) -> None:
        tree = self.problems.tree
        selected = tree.index(tree.selection()[0]) if tree.selection() else 0
        keep = len(tree.get_children()) == len(result.rows)  # the same result again (settings)
        self.stats.show(result.stats)
        for widget in (self.all_good, self.problems_title, self.problems, self.detail):
            widget.pack_forget()
        self.where.show(result.where, after=self.stats)
        if result.rows:
            self.problems_title.pack(anchor="w", pady=(GAP, 0))
            self.problems.pack(fill="both", expand=True, pady=(SPACE, 0))
            self.problems.show(
                [
                    ListRow(row.icon, row.name, (row.detail,), tag=_TAGS.get(row.tone, "warning"))
                    for row in result.rows
                ]  # fmt: skip
            )
            self.detail.pack(side="bottom", fill="x", pady=(SPACE, 0), before=self.problems)
            children = tree.get_children()
            row = children[selected if keep and selected < len(children) else 0]
            tree.selection_set(row)
            tree.focus(row)
            self._show_detail()
        else:
            # Nothing to show and nothing converted (an unexpected error, 038): the headline,
            # never "every file was converted".
            converted = bool(result.stats) and result.stats[0].value > 0
            self._headline = "" if converted else result.headline
            self._all_good_text()
            self.all_good.pack(fill="x", pady=(GAP, 0))

    def forget(self) -> None:
        """The result was dropped (an edit): its figures and list leave the screen; its cards
        wait, faded (014)."""
        self._wait()
        for widget in (self.all_good, self.problems_title, self.problems, self.detail):
            widget.pack_forget()
        self.where.show("")

    def _show_detail(self) -> None:
        row = self.problems.current()
        self.detail.configure(text=f"{row.name}: {row.values[0]}" if row else "")

    def _all_good_text(self) -> None:
        if self._catalog is not None:
            text = self._headline or self._catalog.text("gui.result.all_good")
            self.all_good_text.configure(text=text)

    def _wait(self) -> None:
        names = ("gui.result.stat_converted", "gui.result.stat_skipped", "gui.result.stat_failed")
        catalog = self._catalog
        self.stats.waiting([catalog.text(name) for name in names] if catalog else [])

    def apply_language(self, catalog: Catalog) -> None:
        self._catalog = catalog
        if self.stats.dimmed or not self.stats.figures():
            self._wait()
        for widget, key in self._texts:
            widget.configure(text=catalog.text(key))
        self._all_good_text()
        self.problems.apply_headings(
            catalog.text("gui.main.column_name"),
            [catalog.text("gui.result.column_what")],
            "",
        )

    def apply_palette(self, palette: Palette) -> None:
        self.where.apply_palette(palette)
        self.stats.apply_palette(palette)
        self.problems.apply_palette(palette)

    def _label(self, widget: Any, key: str) -> None:
        self._texts.append((widget, key))
