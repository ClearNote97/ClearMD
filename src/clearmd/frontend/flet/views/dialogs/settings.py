"""The settings dialog: exactly the settings of ADR-0012, Restore defaults, Cancel, Save (UX §7)."""

from collections.abc import Callable
from dataclasses import replace

import flet as ft

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.design.metrics import GAP
from clearmd.frontend.flet.components.dialog import Dialog
from clearmd.frontend.flet.components.primitives import button, label, stretch
from clearmd.frontend.flet.layout.units import CONTROL_WIDTH, SETTINGS_WIDTH
from clearmd.frontend.flet.views.dialogs.split_settings import SplitSettings
from clearmd.frontend.flet.visuals.look import text_style
from clearmd.frontend.flet.visuals.theme import role
from clearmd.i18n import Catalog

_LANGUAGES = {"en": "English", "es": "Español"}  # each in its own language


class SettingsDialog(Dialog):
    """Exactly the settings of ADR-0012, each with one line of explanation; Restore defaults puts
    the controls back to the defaults; Save applies and writes them (UX §7). Split a PDF's group
    follows the images (feature 023)."""

    ROWS = (
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

    def __init__(
        self,
        catalog: Catalog,
        settings: Settings,
        *,
        on_save: Callable[[Settings], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(
            title=catalog.text("gui.settings.title"),
            on_close=on_close,
            width=SETTINGS_WIDTH,
            scrolls=True,  # its rows are many: it scrolls when the window is short
        )
        self._settings = settings
        self._on_save = on_save
        text = catalog.text
        self.choices: dict[str, dict[str, str]] = {
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
        self.controls: dict[str, ft.Dropdown | ft.Checkbox] = {}
        self.split = SplitSettings(catalog)
        rows = ft.Column(spacing=GAP, tight=True)
        for setting, key in self.ROWS:
            name = label("strong", text(f"gui.settings.{key}"))
            cell = ft.Column(
                [name, label("muted", text(f"gui.settings.{key}_help"))], spacing=0, expand=True
            )
            control: ft.Dropdown | ft.Checkbox
            if setting in self.choices:
                control = ft.Dropdown(
                    options=[
                        ft.DropdownOption(key=value, text=shown)
                        for value, shown in self.choices[setting].items()
                    ],
                    width=CONTROL_WIDTH,
                    text_style=text_style("onPage"),
                    bgcolor=role("card"),
                    border_color=role("border"),
                    focused_border_color=role("accent"),
                )
            else:
                control = ft.Checkbox()
            control.tooltip = text(f"gui.settings.{key}")
            holder = ft.Container(content=control, width=CONTROL_WIDTH)  # one column, flush left
            rows.controls.append(
                ft.Row([cell, holder], spacing=GAP, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            )
            self.controls[setting] = control
            if setting == "images":
                rows.controls.extend(self.split.controls)
        self.body.controls.append(rows)
        self._load(settings)
        restore = button("", self.restore, text("gui.settings.restore"))
        cancel = button("", self.close_dialog, text("gui.settings.cancel"))
        save = button("primary", self.save, text("gui.settings.save"))
        self.default(self.save)
        self.foot.controls.extend([restore, stretch(), cancel, save])

    def _load(self, settings: Settings) -> None:
        self.split.load(settings)
        for setting, control in self.controls.items():
            value = getattr(settings, setting)
            if isinstance(control, ft.Dropdown):
                control.value = str(value)
            else:
                control.value = bool(value)

    def chosen(self) -> Settings:
        """The settings as the controls show them (the remembered folder is kept)."""
        changes: dict[str, object] = {}
        for setting, control in self.controls.items():
            if isinstance(control, ft.Dropdown):
                changes[setting] = control.value
            else:
                changes[setting] = bool(control.value)
        chosen = replace(self._settings, **changes)  # type: ignore[arg-type]
        return self.split.chosen(chosen)

    def restore(self) -> None:
        self._load(Settings(last_output_folder=self._settings.last_output_folder))

    def save(self) -> None:
        chosen = self.chosen()
        self.close_dialog()
        self._on_save(chosen)
