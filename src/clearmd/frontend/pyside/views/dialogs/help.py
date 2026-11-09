"""The help dialog (UX §4): the presenter's sections, the same in the three windows (feature 035,
AC-04): what Markdown is, the real flow, the three tools, what is converted, where the results go,
the keyboard, privacy and the language. This window takes dropped files, so Help says so."""

from collections.abc import Callable

from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from clearmd.frontend.design.metrics import GAP, HALF, SPACE
from clearmd.frontend.presenter.screens.help import help_sections
from clearmd.frontend.pyside.components.dialog import Dialog
from clearmd.frontend.pyside.components.primitives import button, label
from clearmd.i18n import Catalog

DROPS = True  # the Qt window takes files dropped from the system (window/inputs.py)
HELP_WIDTH = 720  # wide and short: it fits a 1366 × 768 screen with its taskbar


class HelpDialog(Dialog):
    """``help_sections`` in order, each title strong and its text wrapped; the version."""

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
        shown = help_sections(catalog, drops=DROPS)
        for index, (title, text) in enumerate(shown):
            if index:
                sections.addSpacing(GAP - HALF)
            sections.addWidget(label("strong", title))
            sections.addWidget(label("onPage", text, wrap=True))
        sections.addStretch(1)
        scroll.setWidget(content)
        scroll.setMinimumHeight(420)
        self.body.addWidget(scroll)
        self.titles = [title for title, _ in shown]  # what it says (for tests)
        self.texts = [text for _, text in shown]
        if version:
            self.foot.addWidget(label("hint", catalog.text("gui.help.version", version=version)))
        self.foot.addStretch(1)
        close = button("primary", self.close_dialog)
        close.setText(catalog.text("gui.help.close"))
        self.default(close)
        self.foot.addWidget(close)
