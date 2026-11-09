"""The welcome dialog: the three steps and "Don't show again" (UX §4; AC-14); and the language at
once, two buttons each in its own language (audit v3, F4-05). It redraws in the chosen language
while it stays open."""

from collections.abc import Callable
from functools import partial

from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QWidget

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.pyside.components.dialog import Dialog
from clearmd.frontend.pyside.components.primitives import button, label
from clearmd.i18n import Catalog

LANGUAGES = ("en", "es")


class WelcomeDialog(Dialog):
    """The three steps, the two languages and "Don't show again" (UX §4)."""

    def __init__(
        self,
        parent: QWidget,
        catalog: Catalog,
        steps: tuple[str, ...],
        on_done: Callable[[bool], None],
        on_language: Callable[[str], None] = lambda _language: None,
    ) -> None:
        self.dont_show = QCheckBox()
        super().__init__(parent, title="", on_close=lambda: on_done(not self.dont_show.isChecked()))
        languages = QHBoxLayout()
        languages.setSpacing(SPACE)
        self.languages = {code: button("", partial(on_language, code)) for code in LANGUAGES}
        for widget in self.languages.values():
            languages.addWidget(widget)
        languages.addStretch(1)
        self.body.addLayout(languages)
        self.body.addSpacing(GAP)
        self.intro = label("onPage", wrap=True)
        self.body.addWidget(self.intro)
        self.steps = [label("strong", step, wrap=True) for step in steps]
        for step in self.steps:
            self.body.addSpacing(SPACE)
            self.body.addWidget(step)
        self.body.addSpacing(GAP)
        self.language_line = label("muted", wrap=True)
        self.body.addWidget(self.language_line)
        self.foot.addWidget(self.dont_show)
        self.foot.addStretch(1)
        self.start = button("primary", self.close_dialog)
        self.default(self.start)
        self.foot.addWidget(self.start)
        self.apply_language(catalog)

    def apply_language(self, catalog: Catalog) -> None:
        """Every word again, from ``catalog``: the user has just chosen a language."""
        text = catalog.text
        self.setWindowTitle(text("gui.welcome.title"))
        for code, widget in self.languages.items():
            widget.setText(text(f"gui.welcome.language_{code}"))
        self.intro.setText(text("gui.welcome.intro"))
        for number, step in enumerate(self.steps, start=1):
            step.setText(text(f"gui.welcome.step{number}"))
        self.language_line.setText(text("gui.help.language"))
        self.dont_show.setText(text("gui.welcome.dont_show"))
        self.start.setText(text("gui.welcome.start"))
