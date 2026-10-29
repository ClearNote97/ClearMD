"""Help, welcome and settings (UX §4, §7; AC-13 – AC-15), as dialogs in ClearMD's look."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from dataclasses import replace
from tkinter import ttk

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.ttk.brand import CHECK_ON_PAGE, MUTED, PRIMARY, SOFT, Palette
from clearmd.frontend.ttk.components.dialog import Dialog
from clearmd.frontend.ttk.layout import GAP, HALF, SPACE
from clearmd.i18n import Catalog

_HELP_SECTIONS = ("how", "formats", "where", "privacy", "language")
_LANGUAGES = {"en": "English", "es": "Español"}  # each in its own language


def help_dialog(
    parent: tk.Misc,
    catalog: Catalog,
    palette: Palette,
    fonts: dict[str, tkfont.Font],
    on_close: Callable[[], None],
) -> Dialog:
    """How to use it, what it converts, where results go, privacy, the language (UX §4)."""
    dialog = Dialog(
        parent,
        title=catalog.text("gui.help.title"),
        palette=palette,
        fonts=fonts,
        on_close=on_close,
    )
    for index, section in enumerate(_HELP_SECTIONS):
        title = ttk.Label(dialog.body, text=catalog.text(f"gui.help.{section}_title"))
        title.configure(font=fonts["strong"])
        title.pack(anchor="w", pady=(0 if index == 0 else GAP, 0))
        text = ttk.Label(
            dialog.body, text=catalog.text(f"gui.help.{section}"), wraplength=560, justify="left"
        )
        text.pack(anchor="w", pady=(HALF, 0))
    close = ttk.Button(
        dialog.actions, text=catalog.text("gui.help.close"), style=PRIMARY, command=dialog.close
    )
    close.pack(side="right")
    dialog.bind("<Return>", lambda _event: dialog.close())
    return dialog


class WelcomeDialog(Dialog):
    """The three steps and "Don't show again" (UX §4; AC-14)."""

    def __init__(
        self,
        parent: tk.Misc,
        catalog: Catalog,
        palette: Palette,
        fonts: dict[str, tkfont.Font],
        steps: tuple[str, ...],
        on_done: Callable[[bool], None],
    ) -> None:
        self.dont_show = tk.BooleanVar(value=False)
        super().__init__(
            parent,
            title=catalog.text("gui.welcome.title"),
            palette=palette,
            fonts=fonts,
            on_close=lambda: on_done(not self.dont_show.get()),
            width=560,
        )
        ttk.Label(self.body, text=catalog.text("gui.welcome.intro")).pack(anchor="w")
        for step in steps:
            line = ttk.Label(self.body, text=step, font=fonts["strong"])
            line.pack(anchor="w", pady=(SPACE, 0))
        language = ttk.Label(
            self.body, text=catalog.text("gui.help.language"), style=MUTED, wraplength=480
        )
        language.pack(anchor="w", pady=(GAP, 0))
        check = ttk.Checkbutton(
            self.actions, text=catalog.text("gui.welcome.dont_show"), variable=self.dont_show
        )
        check.configure(style=CHECK_ON_PAGE)
        check.pack(side="left")
        start = ttk.Button(
            self.actions, text=catalog.text("gui.welcome.start"), style=PRIMARY, command=self.close
        )
        start.pack(side="right")
        self.bind("<Return>", lambda _event: self.close())


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
            ("show_welcome", "welcome"),
        )
        self.body.columnconfigure(0, weight=1)
        for row, (setting, key) in enumerate(rows):
            self._row(row, setting, text(f"gui.settings.{key}"), text(f"gui.settings.{key}_help"))
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

    def _row(self, row: int, setting: str, label: str, explanation: str) -> None:
        cell = ttk.Frame(self.body, style="TFrame")
        cell.grid(row=row, column=0, sticky="w", pady=(0 if row == 0 else GAP, 0))
        ttk.Label(cell, text=label, font=self._fonts["strong"]).pack(anchor="w")
        ttk.Label(cell, text=explanation, style=MUTED, wraplength=400).pack(anchor="w")
        if setting in self._choices:
            variable: tk.Variable = tk.StringVar(master=self)
            control: ttk.Widget = ttk.Combobox(
                self.body,
                textvariable=variable,
                values=list(self._choices[setting].values()),
                state="readonly",
                width=24,
            )
        else:
            variable = tk.BooleanVar(master=self)
            control = ttk.Checkbutton(self.body, variable=variable)
        control.grid(row=row, column=1, sticky="e", padx=(GAP, 0), pady=(0 if row == 0 else GAP, 0))
        self.values[setting] = variable

    def _load(self, settings: Settings) -> None:
        for setting, variable in self.values.items():
            value = getattr(settings, setting)
            variable.set(self._choices[setting][value] if setting in self._choices else value)

    def chosen(self) -> Settings:
        """The settings as the controls show them (the remembered folder is kept)."""
        changes: dict[str, object] = {}
        for setting, variable in self.values.items():
            if setting in self._choices:
                shown = variable.get()
                changes[setting] = next(k for k, v in self._choices[setting].items() if v == shown)
            else:
                changes[setting] = bool(variable.get())
        return replace(self._settings, **changes)  # type: ignore[arg-type]

    def restore(self) -> None:
        self._load(Settings(last_output_folder=self._settings.last_output_folder))

    def save(self) -> None:
        chosen = self.chosen()
        self.close()
        self._on_save(chosen)


class KeepInputsDialog(Dialog):
    """ "Convert more": keep the chosen files, or start empty (asked every time, feature 007)."""

    def __init__(
        self,
        parent: tk.Misc,
        catalog: Catalog,
        palette: Palette,
        fonts: dict[str, tkfont.Font],
        on_answer: Callable[[bool], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(
            parent,
            title=catalog.text("gui.more.title"),
            palette=palette,
            fonts=fonts,
            on_close=on_close,
            width=480,
        )
        self._on_answer = on_answer
        ttk.Label(self.body, text=catalog.text("gui.more.question"), font=fonts["strong"]).pack(
            anchor="w"
        )
        explanation = ttk.Label(
            self.body, text=catalog.text("gui.more.explain"), style=MUTED, wraplength=400
        )
        explanation.pack(anchor="w", pady=(SPACE, 0))
        self.keep = ttk.Button(
            self.actions, text=catalog.text("gui.more.keep"), style=PRIMARY,
            command=lambda: self.answer(True),
        )  # fmt: skip
        self.keep.pack(side="right")
        self.clear = ttk.Button(
            self.actions, text=catalog.text("gui.more.clear"), style=SOFT,
            command=lambda: self.answer(False),
        )  # fmt: skip
        self.clear.pack(side="right", padx=(0, SPACE))
        self.bind("<Return>", lambda _event: self.answer(True))

    def answer(self, keep: bool) -> None:
        self.close()
        self._on_answer(keep)
