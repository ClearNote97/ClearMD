"""Settings' "Merge Documents" group (feature 026): into one Markdown or one PDF, saved by the
dialog's Save. A combo box, as the Split group's Keep."""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.design.metrics import GAP
from clearmd.frontend.ttk.visuals.style_names import MUTED
from clearmd.i18n import Catalog

_INTO = ("markdown", "pdf")


class MergeSettings:
    """Its words on the left (column 0), its choice on the right (column 1) of ``body``."""

    def __init__(
        self, body: tk.Misc, row: int, catalog: Catalog, fonts: dict[str, tkfont.Font]
    ) -> None:
        text = catalog.text
        cell = ttk.Frame(body, style="TFrame")
        cell.grid(row=row, column=0, sticky="nw", pady=(GAP, 0))
        ttk.Label(cell, text=text("gui.settings.merge"), font=fonts["strong"]).pack(anchor="w")
        ttk.Label(cell, text=text("gui.settings.merge_help"), style=MUTED, wraplength=400).pack(
            anchor="w"
        )
        self._choices = {value: text(f"gui.merge.{value}") for value in _INTO}
        self.into = tk.StringVar(master=body)
        ttk.Combobox(
            body, textvariable=self.into, values=list(self._choices.values()),
            state="readonly", width=24,
        ).grid(row=row, column=1, sticky="e", padx=(GAP, 0), pady=(GAP, 0))  # fmt: skip

    def load(self, settings: Settings) -> None:
        self.into.set(self._choices[settings.merge_into])

    def chosen(self) -> dict[str, object]:
        shown = self.into.get()
        return {"merge_into": next(k for k, v in self._choices.items() if v == shown)}

    def release(self) -> None:
        """Its Tk variable dies on the UI thread, with the dialog (see ``Dialog.close``)."""
        self.into = None  # type: ignore[assignment]
