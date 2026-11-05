"""The bar at the foot of every page (ADR-0029): why the primary action is disabled, one secondary
action and the page's primary action."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QWidget

from clearmd.frontend.design.metrics import SPACE
from clearmd.frontend.presenter.models import Primary
from clearmd.frontend.pyside.components.primitives import button, label, restyle


class ActionBar(QWidget):
    """The bar at the foot of every page (ADR-0029): why the primary action is disabled, one
    secondary action (Back, Cancel or Convert more), and the page's primary action."""

    def __init__(self, *, on_primary: Callable[[], None]) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACE)
        self.hint = label("hint", wrap=True)
        self.hint.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.hint, 1)
        self.secondary = button("", self._secondary)
        self.secondary.hide()
        layout.addWidget(self.secondary)
        self.primary = button("primary", on_primary)
        self.primary.setDefault(False)
        self.primary.setAutoDefault(False)
        layout.addWidget(self.primary)
        self._command: Callable[[], None] | None = None

    def show(self, primary: Primary) -> None:  # type: ignore[override]  # the presenter's, not QWidget's
        self.primary.setText(primary.label)
        self.primary.setEnabled(primary.enabled)
        self.hint.setText(primary.hint)

    def show_secondary(
        self, text: str | None, command: Callable[[], None] | None = None, *, strong: bool = False
    ) -> None:
        if text is None or command is None:
            self.secondary.hide()
            self._command = None
            return
        self._command = command
        self.secondary.setText(text)
        self.secondary.setObjectName("strong" if strong else "")
        restyle(self.secondary, "strong", strong)
        self.secondary.show()

    def _secondary(self) -> None:
        if self._command is not None:
            self._command()
