"""The dark rail (ADR-0027, ADR-0029): the logo, the steps, Settings, Help, the promise and the
version."""

from collections.abc import Callable
from functools import partial

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from clearmd.frontend.design.metrics import COMPACT_RAIL_WIDTH, GAP, HALF, RAIL_WIDTH, SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.presenter.state import STEPS
from clearmd.frontend.pyside.components.primitives import button, label, restyle
from clearmd.frontend.pyside.components.rail_art import badge, rail_dim
from clearmd.frontend.pyside.layout.units import BADGE, STEP_HEIGHT
from clearmd.frontend.pyside.visuals.images import logo
from clearmd.i18n import Catalog

COMPACT_VERSION_CHARS = 6  # what fits the compact rail at 14 px


class Rail(QFrame):
    """The dark rail (ADR-0027, ADR-0029): the logo, Clear·MD, the four steps — each one can be
    opened, the one on screen highlighted — Settings, Help, the promise and the version. Below
    1000 px of window width it is compact: the mark and the numbers only."""

    def __init__(
        self,
        *,
        on_step: Callable[[int], None],
        on_settings: Callable[[], None],
        on_help: Callable[[], None],
    ) -> None:
        super().__init__()
        self.setObjectName("rail")
        self.setFixedWidth(RAIL_WIDTH)
        self._compact = False
        self._page = 1
        self._labels = [""] * len(STEPS)
        self._words = {"settings": "", "help": ""}
        self._version = ""
        self._local = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE, 3 * SPACE, SPACE, GAP)
        layout.setSpacing(HALF)

        top = QHBoxLayout()
        top.setContentsMargins(SPACE, 0, 0, 0)
        top.setSpacing(SPACE)
        self.mark = QLabel()
        self.mark.setPixmap(logo("clearmd-mark-dark-40"))
        top.addWidget(self.mark)
        self.wordmark = label("wordmark")
        top.addWidget(self.wordmark)
        top.addStretch(1)
        layout.addLayout(top)
        layout.addSpacing(4 * SPACE)

        self.steps: list[QPushButton] = []
        for index in range(1, len(STEPS) + 1):
            step = button("step", partial(on_step, index))
            step.setFixedHeight(STEP_HEIGHT)
            step.setIconSize(QSize(BADGE, BADGE))
            layout.addWidget(step)
            self.steps.append(step)
        layout.addStretch(1)
        self.settings = button("railButton", on_settings)
        self.help = button("railButton", on_help)
        for widget in (self.settings, self.help):
            widget.setFixedHeight(STEP_HEIGHT)
            layout.addWidget(widget)
        self.foot = label("local", wrap=True)
        self.foot.setContentsMargins(SPACE, SPACE, SPACE, 0)
        layout.addWidget(self.foot)
        self._palette: Palette | None = None

    def apply_language(self, catalog: Catalog) -> None:
        self._labels = [catalog.text(f"gui.steps.{name}") for name in STEPS]
        self._words = {
            "settings": catalog.text("gui.main.settings"),
            "help": catalog.text("gui.main.help_word"),
        }
        self._local = catalog.text("gui.app.local")
        self._draw()

    def apply_palette(self, palette: Palette) -> None:
        self._palette = palette
        self.wordmark.setText(
            f'Clear<span style="color:{palette.clear}">·</span>MD'
        )  # the "Clear" tone between the two words
        self._draw()

    def show_page(self, page: int) -> None:
        if page != self._page:
            self._page = page
            self._draw()

    def show_version(self, version: str) -> None:
        self._version = f"v{version}" if version[:1].isdigit() else version
        self._draw()

    def set_compact(self, compact: bool) -> None:
        if compact != self._compact:
            self._compact = compact
            self.setFixedWidth(COMPACT_RAIL_WIDTH if compact else RAIL_WIDTH)
            self.wordmark.setVisible(not compact)
            self.foot.setWordWrap(not compact)
            self.foot.setAlignment(
                Qt.AlignmentFlag.AlignCenter
                if compact
                else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            restyle(self, "compact", "true" if compact else "false")
            self._draw()

    @property
    def compact(self) -> bool:
        return self._compact

    def step_texts(self) -> list[str]:
        """The steps as shown, the one on screen marked with ``>`` (for tests)."""
        return [
            ("> " if index + 1 == self._page else "") + text
            for index, text in enumerate(self._labels)
        ]

    def _draw(self) -> None:
        palette = self._palette
        for index, step in enumerate(self.steps, start=1):
            current = index == self._page
            text = self._labels[index - 1]
            step.setText("" if self._compact else f" {text}")
            step.setToolTip(text)
            step.setAccessibleName(text)
            if palette is not None:
                colour = palette.on_accent if current else rail_dim(palette)
                fill = palette.accent if current else palette.rail
                step.setIcon(QIcon(badge(index, colour, fill)))
            restyle(step, "current", "true" if current else "false")
        self.settings.setText("⚙" if self._compact else self._words["settings"])
        self.help.setText("?" if self._compact else self._words["help"])
        for widget, word in ((self.settings, "settings"), (self.help, "help")):
            widget.setToolTip(self._words[word])
            widget.setAccessibleName(self._words[word])
        self.foot.setText(
            self._compact_version()
            if self._compact
            else "\n".join(filter(None, (self._local, self._version)))
        )

    def _compact_version(self) -> str:
        """The version in the narrow rail: without its "v" when it would not fit (0.10.1)."""
        return self._version if len(self._version) <= COMPACT_VERSION_CHARS else self._version[1:]
