"""The welcome dialog: the three steps and "Don't show again" (UX §4; AC-14)."""

from collections.abc import Callable

from PySide6.QtWidgets import QCheckBox, QWidget

from clearmd.frontend.design.metrics import GAP, SPACE
from clearmd.frontend.pyside.components.dialog import Dialog
from clearmd.frontend.pyside.components.primitives import button, label
from clearmd.i18n import Catalog


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
