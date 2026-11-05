"""The help dialog: how to use it, what it converts, where results go, privacy, the language
(UX §4)."""

from collections.abc import Callable

from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from clearmd.frontend.design.metrics import GAP, HALF, SPACE
from clearmd.frontend.pyside.components.dialog import Dialog
from clearmd.frontend.pyside.components.primitives import button, label
from clearmd.i18n import Catalog

_HELP_SECTIONS = ("how", "formats", "where", "keyboard", "privacy", "language")
HELP_WIDTH = 720  # wide and short: it fits a 1366 × 768 screen with its taskbar


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
