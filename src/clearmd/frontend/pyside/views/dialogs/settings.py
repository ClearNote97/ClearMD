"""The settings dialog: exactly the settings of ADR-0012, Restore defaults, Cancel, Save (UX §7)."""

from collections.abc import Callable
from dataclasses import replace

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QVBoxLayout, QWidget

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.pyside.components.dialog import Dialog
from clearmd.frontend.pyside.components.primitives import button, label
from clearmd.frontend.pyside.views.dialogs.split_settings import SplitSettings
from clearmd.i18n import Catalog

CONTROL_WIDTH = 28 * SPACE  # the combo boxes' column (their style sheet makes them 24 * 8 wide)
_LANGUAGES = {"en": "English", "es": "Español"}  # each in its own language
SPLIT_BEFORE = "merge_into"  # Split's group goes after the conversion's settings, before Merge


class SettingsDialog(Dialog):
    """Exactly the settings of ADR-0012, each with one line of explanation; Restore defaults puts
    the controls back to the defaults; Save applies and writes them (UX §7)."""

    ROWS = (
        ("language", "language"),
        ("theme", "theme"),
        ("open_output_when_done", "open_when_done"),
        ("on_existing_output", "existing"),
        ("recursive", "recursive"),
        ("html_strategy", "html"),
        ("summary_format", "summary"),
        ("images", "images"),
        ("merge_into", "merge"),  # after Split's group (feature 026)
        ("show_welcome", "welcome"),
    )

    def __init__(
        self,
        parent: QWidget,
        catalog: Catalog,
        settings: Settings,
        *,
        on_save: Callable[[Settings], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(
            parent, title=catalog.text("gui.settings.title"), on_close=on_close, width=720
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
            "merge_into": {v: text(f"gui.merge.{v}") for v in ("markdown", "pdf")},
        }
        self.controls: dict[str, QComboBox | QCheckBox] = {}
        rows = QVBoxLayout()
        rows.setSpacing(GAP)
        for setting, key in self.ROWS:
            if setting == SPLIT_BEFORE:
                self.split = SplitSettings(rows, catalog, CONTROL_WIDTH)
            row = QHBoxLayout()  # a box, not a grid: its wrapped lines get their height
            row.setSpacing(GAP)
            cell = QWidget()
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(0)
            name = label("strong", text(f"gui.settings.{key}"))
            cell_layout.addWidget(name)
            cell_layout.addWidget(label("muted", text(f"gui.settings.{key}_help"), wrap=True))
            row.addWidget(cell, 1)
            control: QComboBox | QCheckBox
            if setting in self._choices:
                combo = QComboBox()
                combo.addItems(list(self._choices[setting].values()))
                control = combo
            else:
                control = QCheckBox()
            control.setAccessibleName(text(f"gui.settings.{key}"))
            name.setBuddy(control)
            holder = QWidget()  # the controls share one column, flush left
            holder.setFixedWidth(CONTROL_WIDTH)
            holder_layout = QHBoxLayout(holder)
            holder_layout.setContentsMargins(0, 0, 0, 0)
            holder_layout.addWidget(control)
            holder_layout.addStretch(1 if isinstance(control, QCheckBox) else 0)
            row.addWidget(holder, 0, Qt.AlignmentFlag.AlignVCenter)
            rows.addLayout(row)
            self.controls[setting] = control
        self.body.addLayout(rows)
        self._load(settings)

        restore = button("", self.restore)
        restore.setText(text("gui.settings.restore"))
        self.foot.addWidget(restore)
        self.foot.addStretch(1)
        cancel = button("", self.reject)
        cancel.setText(text("gui.settings.cancel"))
        self.foot.addWidget(cancel)
        save = button("primary", self.save)
        save.setText(text("gui.settings.save"))
        self.default(save)
        self.foot.addWidget(save)

    def _load(self, settings: Settings) -> None:
        self.split.load(settings)
        for setting, control in self.controls.items():
            value = getattr(settings, setting)
            if isinstance(control, QComboBox):
                control.setCurrentText(self._choices[setting][value])
            else:
                control.setChecked(bool(value))

    def chosen(self) -> Settings:
        """The settings as the controls show them (the remembered folder is kept)."""
        changes: dict[str, object] = self.split.chosen()
        for setting, control in self.controls.items():
            if isinstance(control, QComboBox):
                shown = control.currentText()
                changes[setting] = next(k for k, v in self._choices[setting].items() if v == shown)
            else:
                changes[setting] = control.isChecked()
        return replace(self._settings, **changes)  # type: ignore[arg-type]

    def restore(self) -> None:
        self._load(Settings(last_output_folder=self._settings.last_output_folder))

    def save(self) -> None:
        chosen = self.chosen()
        self.close_dialog()
        self._on_save(chosen)
