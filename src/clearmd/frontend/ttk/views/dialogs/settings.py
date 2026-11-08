"""The settings dialog: exactly the settings of ADR-0012 (UX §7; AC-15), and the groups of Split
and Merge (features 023, 026)."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from dataclasses import replace
from tkinter import ttk

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.design.metrics import GAP, MIN_HEIGHT, SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.ttk.components.dialog import Dialog
from clearmd.frontend.ttk.components.scroll_area import ScrollArea
from clearmd.frontend.ttk.views.dialogs.merge_settings import MergeSettings
from clearmd.frontend.ttk.views.dialogs.split_settings import SplitSettings
from clearmd.frontend.ttk.visuals.style_names import MUTED, PRIMARY, SOFT
from clearmd.i18n import Catalog

_LANGUAGES = {"en": "English", "es": "Español"}  # each in its own language


class SettingsDialog(Dialog):
    """Exactly the settings of ADR-0012, each with one line of explanation; Restore defaults
    puts the controls back to the defaults; Save applies and writes them (UX §7; AC-15)."""

    def __init__(
        self,
        parent: tk.Misc,
        catalog: Catalog,
        palette: Palette,
        fonts: dict[str, tkfont.Font],
        settings: Settings,
        on_save: Callable[[Settings], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(
            parent,
            title=catalog.text("gui.settings.title"),
            palette=palette,
            fonts=fonts,
            on_close=on_close,
            width=720,
        )
        self._settings = settings
        self._on_save = on_save
        text = catalog.text
        self._choices: dict[str, dict[str, str]] = {
            "language": dict(_LANGUAGES),
            "theme": {v: text(f"gui.settings.theme_{v}") for v in ("system", "light", "dark")},
            "on_existing_output": {
                v: text(f"gui.settings.existing_{v}") for v in ("ask", "overwrite", "skip")
            },
            "html_strategy": {v: text(f"gui.settings.html_{v}") for v in ("full", "article")},
            "summary_format": {
                v: text(f"gui.settings.summary_{v}") for v in ("markdown", "markdown_pdf", "pdf")
            },
            "images": {v: text(f"gui.settings.images_{v}") for v in ("omit", "folder")},
        }
        self.values: dict[str, tk.Variable] = {}
        self._fonts = fonts
        rows = (
            ("language", "language"),
            ("theme", "theme"),
            ("open_output_when_done", "open_when_done"),
            ("on_existing_output", "existing"),
            ("recursive", "recursive"),
            ("html_strategy", "html"),
            ("summary_format", "summary"),
            ("images", "images"),
            ("show_welcome", "welcome"),
        )
        # The rows scroll when the dialog would be taller than the window (feature 023).
        self._area = ScrollArea(self.body, ground=palette.card)
        self._area.pack(fill="both", expand=True)
        self._rows = self._area.inner
        self._rows.columnconfigure(0, weight=1)
        for row, (setting, key) in enumerate(rows):
            self._row(row, setting, text(f"gui.settings.{key}"), text(f"gui.settings.{key}_help"))
        self.split = SplitSettings(self._rows, len(rows), catalog, fonts)
        self.merge = MergeSettings(self._rows, len(rows) + 1, catalog, fonts)  # 026
        self._load(settings)

        save = ttk.Button(
            self.actions, text=text("gui.settings.save"), style=PRIMARY, command=self.save
        )
        save.pack(side="right")
        cancel = ttk.Button(
            self.actions, text=text("gui.settings.cancel"), style=SOFT, command=self.close
        )
        cancel.pack(side="right", padx=(0, SPACE))
        restore = ttk.Button(
            self.actions, text=text("gui.settings.restore"), style=SOFT, command=self.restore
        )
        restore.pack(side="left")
        self.bind("<Return>", lambda _event: self.save())
        self._fit(parent)

    def _fit(self, parent: tk.Misc) -> None:
        """The rows at most as tall as the window leaves them (the screen, before it shows)."""
        self.update_idletasks()
        window = parent.winfo_toplevel().winfo_height()
        room = window if window > MIN_HEIGHT // 2 else self.winfo_screenheight()
        chrome = self.winfo_reqheight() - self._area.winfo_reqheight()
        self._area.fit(max(room - chrome - 2 * GAP, 12 * GAP))

    def _row(self, row: int, setting: str, label: str, explanation: str) -> None:
        cell = ttk.Frame(self._rows, style="TFrame")
        cell.grid(row=row, column=0, sticky="w", pady=(0 if row == 0 else GAP, 0))
        ttk.Label(cell, text=label, font=self._fonts["strong"]).pack(anchor="w")
        ttk.Label(cell, text=explanation, style=MUTED, wraplength=400).pack(anchor="w")
        if setting in self._choices:
            variable: tk.Variable = tk.StringVar(master=self)
            control: ttk.Widget = ttk.Combobox(
                self._rows,
                textvariable=variable,
                values=list(self._choices[setting].values()),
                state="readonly",
                width=24,
            )
        else:
            variable = tk.BooleanVar(master=self)
            control = ttk.Checkbutton(self._rows, variable=variable)
        control.grid(row=row, column=1, sticky="e", padx=(GAP, 0), pady=(0 if row == 0 else GAP, 0))
        self.values[setting] = variable

    def _load(self, settings: Settings) -> None:
        for setting, variable in self.values.items():
            value = getattr(settings, setting)
            variable.set(self._choices[setting][value] if setting in self._choices else value)
        self.split.load(settings)
        self.merge.load(settings)

    def chosen(self) -> Settings:
        """The settings as the controls show them (the remembered folder is kept)."""
        changes: dict[str, object] = {}
        for setting, variable in self.values.items():
            if setting in self._choices:
                shown = variable.get()
                changes[setting] = next(k for k, v in self._choices[setting].items() if v == shown)
            else:
                changes[setting] = bool(variable.get())
        changes.update(self.split.chosen())
        changes.update(self.merge.chosen())
        return replace(self._settings, **changes)  # type: ignore[arg-type]

    def restore(self) -> None:
        self._load(Settings(last_output_folder=self._settings.last_output_folder))

    def close(self) -> None:
        self.split.release()
        self.merge.release()
        super().close()

    def save(self) -> None:
        chosen = self.chosen()
        self.close()
        self._on_save(chosen)
