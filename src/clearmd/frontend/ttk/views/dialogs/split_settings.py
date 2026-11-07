"""Settings' "Split a PDF" group (feature 023, AC-10): into N parts or every N pages, the two
numbers, and what to keep. The same choices as step 1 of Split, saved by the dialog's Save."""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from clearmd.backend.schemas.settings import RANGES, Settings
from clearmd.frontend.design.metrics import GAP, HALF
from clearmd.frontend.ttk.visuals.style_names import MUTED
from clearmd.i18n import Catalog

_KEEP = ("pdf", "markdown", "both")


class SplitSettings:
    """Its words on the left (column 0), its controls on the right (column 1) of ``body``."""

    def __init__(
        self, body: tk.Misc, row: int, catalog: Catalog, fonts: dict[str, tkfont.Font]
    ) -> None:
        text = catalog.text
        cell = ttk.Frame(body, style="TFrame")
        cell.grid(row=row, column=0, sticky="nw", pady=(GAP, 0))
        ttk.Label(cell, text=text("gui.settings.split"), font=fonts["strong"]).pack(anchor="w")
        ttk.Label(cell, text=text("gui.settings.split_help"), style=MUTED, wraplength=400).pack(
            anchor="w"
        )
        controls = ttk.Frame(body, style="TFrame")
        controls.grid(row=row, column=1, sticky="e", padx=(GAP, 0), pady=(GAP, 0))
        controls.columnconfigure(0, weight=1)
        self.cut = tk.StringVar(master=body, value="parts")
        self.numbers: dict[str, ttk.Spinbox] = {}
        for line, name in enumerate(("parts", "pages")):
            ttk.Radiobutton(
                controls, variable=self.cut, value=name, text=text(f"gui.settings.split_{name}")
            ).grid(row=line, column=0, sticky="w", pady=(0 if line == 0 else HALF, 0))
            low, high = RANGES[f"split_{name}"]
            number = ttk.Spinbox(controls, from_=low, to=high, increment=1, width=6)
            number.grid(
                row=line, column=1, sticky="e", padx=(GAP, 0), pady=(0 if line == 0 else HALF, 0)
            )
            self.numbers[name] = number
        self._keeps = {value: text(f"gui.split.keep_{value}") for value in _KEEP}
        ttk.Label(controls, text=text("gui.settings.split_keep")).grid(
            row=2, column=0, sticky="w", pady=(HALF, 0)
        )
        self.keep = tk.StringVar(master=body)
        ttk.Combobox(
            controls, textvariable=self.keep, values=list(self._keeps.values()),
            state="readonly", width=18,
        ).grid(row=2, column=1, sticky="e", padx=(GAP, 0), pady=(HALF, 0))  # fmt: skip
        self._settings = Settings()

    def load(self, settings: Settings) -> None:
        self._settings = settings
        self.cut.set(settings.split_cut)
        for name, number in self.numbers.items():
            number.delete(0, "end")
            number.insert(0, str(getattr(settings, f"split_{name}")))
        self.keep.set(self._keeps[settings.split_keep])

    def chosen(self) -> dict[str, object]:
        """The group's settings as its controls show them; a number that is not one, or out of
        its range, keeps the value loaded."""
        changes: dict[str, object] = {"split_cut": self.cut.get()}
        for name, number in self.numbers.items():
            setting = f"split_{name}"
            low, high = RANGES[setting]
            try:
                value = int(number.get().strip())
            except ValueError:
                value = getattr(self._settings, setting)
            changes[setting] = value if low <= value <= high else getattr(self._settings, setting)
        shown = self.keep.get()
        changes["split_keep"] = next(k for k, v in self._keeps.items() if v == shown)
        return changes

    def release(self) -> None:
        """Its Tk variables die on the UI thread, with the dialog (see ``Dialog.close``)."""
        self.cut = self.keep = None  # type: ignore[assignment]
