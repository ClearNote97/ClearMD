"""Help, welcome, settings and "Convert more" (UX §4, §7), as Qt dialogs in ClearMD's look.

Each is modal; Esc closes it (Qt's own reject) and Enter runs its default button."""

from collections.abc import Callable
from dataclasses import replace

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.design.metrics import GAP, HALF, SPACE
from clearmd.frontend.pyside.widgets import button, label
from clearmd.i18n import Catalog

_HELP_SECTIONS = ("how", "formats", "where", "keyboard", "privacy", "language")
_LANGUAGES = {"en": "English", "es": "Español"}  # each in its own language
HELP_WIDTH = 720  # wide and short: it fits a 1366 × 768 screen with its taskbar


class Dialog(QDialog):
    """A body and a row of actions at the foot; ``on_close`` once, however it is closed."""

    def __init__(
        self, parent: QWidget, *, title: str, on_close: Callable[[], None], width: int = 560
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(width)
        self._on_close = on_close
        self._closed = False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(3 * SPACE, 3 * SPACE, 3 * SPACE, 3 * SPACE)
        outer.setSpacing(3 * SPACE)
        self.body = QVBoxLayout()
        self.body.setSpacing(0)
        outer.addLayout(self.body, 1)
        self.foot = QHBoxLayout()
        self.foot.setSpacing(SPACE)
        outer.addLayout(self.foot)
        self.finished.connect(lambda _result: self._finish())

    def _finish(self) -> None:
        if not self._closed:
            self._closed = True
            self._on_close()

    def close_dialog(self) -> None:
        self.done(QDialog.DialogCode.Accepted)

    def default(self, widget: QPushButton) -> None:
        widget.setDefault(True)
        widget.setAutoDefault(True)


class HelpDialog(Dialog):
    """How to use it, what it converts, where results go, privacy, the language; the version."""

    def __init__(
        self, parent: QWidget, catalog: Catalog, on_close: Callable[[], None], *, version: str = ""
    ) -> None:
        super().__init__(
            parent, title=catalog.text("gui.help.title"), on_close=on_close, width=HELP_WIDTH + 64
        )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        sections = QVBoxLayout(content)
        sections.setContentsMargins(0, 0, SPACE, 0)
        sections.setSpacing(HALF)
        for index, section in enumerate(_HELP_SECTIONS):
            if index:
                sections.addSpacing(GAP - HALF)
            sections.addWidget(label("strong", catalog.text(f"gui.help.{section}_title")))
            sections.addWidget(label("onPage", catalog.text(f"gui.help.{section}"), wrap=True))
        sections.addStretch(1)
        scroll.setWidget(content)
        scroll.setMinimumHeight(420)
        self.body.addWidget(scroll)
        self.texts = [
            catalog.text(f"gui.help.{section}") for section in _HELP_SECTIONS
        ]  # what it says (for tests)
        if version:
            self.foot.addWidget(label("hint", catalog.text("gui.help.version", version=version)))
        self.foot.addStretch(1)
        close = button("primary", self.close_dialog)
        close.setText(catalog.text("gui.help.close"))
        self.default(close)
        self.foot.addWidget(close)


class WelcomeDialog(Dialog):
    """The three steps and "Don't show again" (UX §4)."""

    def __init__(
        self,
        parent: QWidget,
        catalog: Catalog,
        steps: tuple[str, ...],
        on_done: Callable[[bool], None],
    ) -> None:
        self.dont_show = QCheckBox(catalog.text("gui.welcome.dont_show"))
        super().__init__(
            parent,
            title=catalog.text("gui.welcome.title"),
            on_close=lambda: on_done(not self.dont_show.isChecked()),
        )
        self.body.addWidget(label("onPage", catalog.text("gui.welcome.intro"), wrap=True))
        for step in steps:
            self.body.addSpacing(SPACE)
            self.body.addWidget(label("strong", step, wrap=True))
        self.body.addSpacing(GAP)
        self.body.addWidget(label("muted", catalog.text("gui.help.language"), wrap=True))
        self.foot.addWidget(self.dont_show)
        self.foot.addStretch(1)
        start = button("primary", self.close_dialog)
        start.setText(catalog.text("gui.welcome.start"))
        self.default(start)
        self.foot.addWidget(start)


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
                v: text(f"gui.settings.summary_{v}") for v in ("markdown", "markdown_pdf")
            },
            "images": {v: text(f"gui.settings.images_{v}") for v in ("omit", "folder")},
        }
        self.controls: dict[str, QComboBox | QCheckBox] = {}
        grid = QGridLayout()
        grid.setHorizontalSpacing(GAP)
        grid.setVerticalSpacing(GAP)
        grid.setColumnStretch(0, 1)
        for row, (setting, key) in enumerate(self.ROWS):
            cell = QWidget()  # a widget, not a layout: its wrapped lines get their height
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(0)
            name = label("strong", text(f"gui.settings.{key}"))
            cell_layout.addWidget(name)
            cell_layout.addWidget(label("muted", text(f"gui.settings.{key}_help"), wrap=True))
            grid.addWidget(cell, row, 0)
            control: QComboBox | QCheckBox
            if setting in self._choices:
                combo = QComboBox()
                combo.addItems(list(self._choices[setting].values()))
                control = combo
            else:
                control = QCheckBox()
            control.setAccessibleName(text(f"gui.settings.{key}"))
            name.setBuddy(control)
            grid.addWidget(control, row, 1)
            self.controls[setting] = control
        self.body.addLayout(grid)
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
        for setting, control in self.controls.items():
            value = getattr(settings, setting)
            if isinstance(control, QComboBox):
                control.setCurrentText(self._choices[setting][value])
            else:
                control.setChecked(bool(value))

    def chosen(self) -> Settings:
        """The settings as the controls show them (the remembered folder is kept)."""
        changes: dict[str, object] = {}
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


class KeepInputsDialog(Dialog):
    """ "Convert more": keep the chosen files, or start empty (asked every time, feature 007)."""

    def __init__(
        self,
        parent: QWidget,
        catalog: Catalog,
        *,
        on_answer: Callable[[bool], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(parent, title=catalog.text("gui.more.title"), on_close=on_close, width=480)
        self._on_answer = on_answer
        self.body.addWidget(label("strong", catalog.text("gui.more.question"), wrap=True))
        self.body.addSpacing(SPACE)
        self.body.addWidget(label("muted", catalog.text("gui.more.explain"), wrap=True))
        self.foot.addStretch(1)
        self.clear = button("", lambda: self.answer(False))
        self.clear.setText(catalog.text("gui.more.clear"))
        self.foot.addWidget(self.clear)
        self.keep = button("primary", lambda: self.answer(True))
        self.keep.setText(catalog.text("gui.more.keep"))
        self.default(self.keep)
        self.foot.addWidget(self.keep)

    def answer(self, keep: bool) -> None:
        self.close_dialog()
        self._on_answer(keep)
