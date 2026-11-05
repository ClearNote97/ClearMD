"""The Qt window's pieces (ADR-0027, ADR-0038): the rail, the ground with its header, the action
bar, a numbered list of files, the figures, the drop zone. Each draws what it is given; none of
them knows the presenter."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import partial
from typing import Any

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QMouseEvent, QPainter, QPaintEvent, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clearmd.frontend.design.colors import blend
from clearmd.frontend.design.metrics import COMPACT_RAIL_WIDTH, GAP, HALF, RAIL_WIDTH, SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.presenter.models import Primary, Stat
from clearmd.frontend.presenter.state import STEPS
from clearmd.frontend.pyside.layout.units import BADGE, ICON, STEP_HEIGHT
from clearmd.frontend.pyside.visuals.images import icon, logo
from clearmd.i18n import Catalog


def label(name: str, text: str = "", *, wrap: bool = False) -> QLabel:
    widget = QLabel(text)
    widget.setObjectName(name)
    widget.setWordWrap(wrap)
    return widget


def button(name: str, on_click: Callable[[], None] | None = None) -> QPushButton:
    widget = QPushButton()
    if name:
        widget.setObjectName(name)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    if on_click is not None:
        widget.clicked.connect(lambda _checked=False: on_click())
    return widget


def card(
    *, padding: int = GAP, horizontal: bool = False
) -> tuple[QFrame, QVBoxLayout | QHBoxLayout]:
    """A rounded card and its layout, with ``padding`` on every side."""
    frame = QFrame()
    frame.setObjectName("card")
    layout: QVBoxLayout | QHBoxLayout = QHBoxLayout(frame) if horizontal else QVBoxLayout(frame)
    layout.setContentsMargins(padding, padding, padding, padding)
    layout.setSpacing(SPACE)
    return frame, layout


def restyle(widget: QWidget, name: str, value: Any) -> None:
    """Set a property the style sheet reads, and draw the widget again with it."""
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    for child in widget.findChildren(QWidget):
        child.style().unpolish(child)
        child.style().polish(child)


# --- The rail --------------------------------------------------------------------------------


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
        layout.addSpacing(5 * SPACE)

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
                colour = palette.on_accent if current else _rail_dim(palette)
                fill = palette.accent if current else palette.rail
                step.setIcon(QIcon(_badge(index, colour, fill)))
            restyle(step, "current", "true" if current else "false")
        self.settings.setText("⚙" if self._compact else self._words["settings"])
        self.help.setText("?" if self._compact else self._words["help"])
        for widget, word in ((self.settings, "settings"), (self.help, "help")):
            widget.setToolTip(self._words[word])
            widget.setAccessibleName(self._words[word])
        self.foot.setText(
            self._version
            if self._compact
            else "\n".join(filter(None, (self._local, self._version)))
        )


def _rail_dim(palette: Palette) -> str:
    return blend(palette.rail_text, palette.rail, 0.55)


def _badge(number: int, colour: str, fill: str) -> QPixmap:
    """A step's number in its circle, drawn at twice the size for sharp edges."""
    scale = 2
    pixmap = QPixmap(BADGE * scale, BADGE * scale)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = painter.pen()
    pen.setColor(QColor(colour))
    pen.setWidthF(1.5 * scale)
    painter.setPen(pen)
    painter.setBrush(QColor(fill))
    margin = scale
    painter.drawEllipse(QRectF(margin, margin, (BADGE - 2) * scale, (BADGE - 2) * scale))
    font = painter.font()
    font.setPixelSize(13 * scale)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, str(number))
    painter.end()
    pixmap.setDevicePixelRatio(scale)
    return pixmap


# --- The ground and its header ---------------------------------------------------------------


class Ground(QWidget):
    """The working area: its soft shape at the top right, the header (step, title, subtitle)."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ground")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._shape = QColor("#D7EEEA")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(GAP, GAP, GAP, GAP)
        layout.setSpacing(HALF)
        self.eyebrow = label("eyebrow")
        self.title = label("title")
        self.subtitle = label("subtitle", wrap=True)
        for widget in (self.eyebrow, self.title, self.subtitle):
            layout.addWidget(widget)
        layout.addSpacing(SPACE)
        self.body = QVBoxLayout()
        self.body.setSpacing(0)
        layout.addLayout(self.body, 1)

    def apply_palette(self, palette: Palette) -> None:
        self._shape = QColor(palette.shape)
        self.update()

    def show_header(self, *, eyebrow: str, title: str, subtitle: str) -> None:
        self.eyebrow.setText(eyebrow)
        self.title.setText(title)
        self.subtitle.setText(subtitle)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 -- Qt's name
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._shape)
        width = self.width()
        painter.drawEllipse(QRectF(width - 380, -260, 640, 360))
        painter.drawEllipse(QRectF(width - 560, -300, 380, 360))
        painter.end()
        super().paintEvent(event)


# --- The action bar --------------------------------------------------------------------------


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


# --- A list of files -------------------------------------------------------------------------


@dataclass(frozen=True)
class ListRow:
    icon: str
    name: str
    values: tuple[str, ...]  # one per extra column
    warning: bool = False  # drawn in the warning colour
    payload: Any = None  # what the row stands for (a path), returned by ``selected``


class FileList(QFrame):
    """``#``, the file's icon and name, then the extra columns; a message in place of an empty
    list. ``checks``: a box on each row, for a list whose selection does something (Choose's
    Remove selected); a list to read has none (feature 014)."""

    selection_changed = Signal()

    def __init__(self, columns: int, *, checks: bool = False, widths: Sequence[int] = ()) -> None:
        super().__init__()
        self.checks = checks
        self._rows: tuple[ListRow, ...] = ()
        self._warning = QColor("#B45309")
        self._stack = QStackedLayout(self)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2 + columns)
        self.tree.setRootIsDecorated(False)
        self.tree.setUniformRowHeights(True)
        self.tree.setIconSize(QSize(ICON, ICON))
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        header = self.tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tree.setColumnWidth(0, 7 * SPACE if checks else 5 * SPACE)
        for column, width in enumerate(widths, start=1):
            self.tree.setColumnWidth(column, width)
        self.tree.itemSelectionChanged.connect(self._selection_changed)
        self.tree.itemChanged.connect(self._checked)
        self._stack.addWidget(self.tree)
        self.empty = label("empty", wrap=True)
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        holder, holder_layout = card()
        holder_layout.addWidget(self.empty)
        self._stack.addWidget(holder)
        self._syncing = False
        self._stack.setCurrentIndex(1)

    def apply_headings(self, headings: Sequence[str], empty: str) -> None:
        self.tree.setHeaderLabels(["#", *headings])
        self.empty.setText(empty)
        self._stack.setCurrentIndex(0 if self._rows or not empty else 1)

    def apply_palette(self, palette: Palette) -> None:
        self._warning = QColor(palette.warning)
        self.show_rows(self._rows)

    def show_rows(self, rows: Sequence[ListRow]) -> None:
        self._rows = tuple(rows)
        self._syncing = True
        self.tree.clear()
        for number, row in enumerate(self._rows, start=1):
            item = QTreeWidgetItem([str(number), row.name, *row.values])
            item.setIcon(1, icon(row.icon))
            item.setData(0, Qt.ItemDataRole.UserRole, number - 1)
            if self.checks:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(0, Qt.CheckState.Unchecked)
            for column in range(1, 2 + len(row.values)):
                item.setToolTip(column, item.text(column))
                if row.warning:
                    item.setForeground(column, self._warning)
            self.tree.addTopLevelItem(item)
        self._syncing = False
        self._stack.setCurrentIndex(0 if self._rows or not self.empty.text() else 1)

    def rows(self) -> tuple[ListRow, ...]:
        return self._rows

    def selected_rows(self) -> list[ListRow]:
        indexes = sorted(
            int(item.data(0, Qt.ItemDataRole.UserRole)) for item in self.tree.selectedItems()
        )
        return [self._rows[index] for index in indexes]

    def selected(self) -> list[Any]:
        """What the selected rows stand for (their payloads)."""
        return [row.payload for row in self.selected_rows()]

    def current(self) -> ListRow | None:
        chosen = self.selected_rows()
        return chosen[0] if chosen else None

    def select(self, index: int) -> None:
        item = self.tree.topLevelItem(index)
        if item is not None:
            self.tree.setCurrentItem(item)

    def clear_selection(self) -> None:
        self.tree.clearSelection()

    def _selection_changed(self) -> None:
        """The boxes follow the selection (feature 007)."""
        if self.checks:
            self._syncing = True
            for index in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(index)
                if item is not None:
                    state = Qt.CheckState.Checked if item.isSelected() else Qt.CheckState.Unchecked
                    item.setCheckState(0, state)
            self._syncing = False
        self.selection_changed.emit()

    def _checked(self, item: QTreeWidgetItem, column: int) -> None:
        """A box clicked: its row joins or leaves the selection."""
        if self._syncing or column != 0:
            return
        item.setSelected(item.checkState(0) == Qt.CheckState.Checked)


# --- The figures -----------------------------------------------------------------------------


class Stats(QWidget):
    """One card per figure, side by side; the figure in its tone, its label below. Before there is
    anything to count, the cards wait faded with "—" (feature 014)."""

    def __init__(self) -> None:
        super().__init__()
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(GAP)
        self._cards: list[tuple[QLabel, QLabel]] = []
        self.dimmed = False

    def show_stats(self, stats: Sequence[Stat]) -> None:
        self._fill([(str(stat.value), stat.label, stat.tone.value) for stat in stats], dim=False)

    def waiting(self, labels: Sequence[str]) -> None:
        self._fill([("—", name, "neutral") for name in labels], dim=True)

    def figures(self) -> list[tuple[str, str]]:
        """The figures as shown (for tests): (label, figure)."""
        return [(name.text(), figure.text()) for figure, name in self._cards]

    def _fill(self, cards: Sequence[tuple[str, str, str]], *, dim: bool) -> None:
        while self._layout.count():
            child = self._layout.takeAt(0)
            widget = child.widget() if child is not None else None
            if widget is not None:
                widget.deleteLater()
        self._cards.clear()
        self.dimmed = dim
        for figure_text, name_text, tone in cards:
            frame, layout = card()
            frame.setProperty("dim", "true" if dim else "false")
            layout.setSpacing(HALF)
            figure = label("figure", figure_text)
            figure.setProperty("tone", "neutral" if dim else tone)
            name = label("muted", name_text)
            layout.addWidget(figure)
            layout.addWidget(name)
            self._layout.addWidget(frame, 1)
            self._cards.append((figure, name))


# --- The drop zone ---------------------------------------------------------------------------


class DropZone(QFrame):
    """Where files and folders can be dropped (the whole window takes them); a click adds files."""

    def __init__(self, *, on_click: Callable[[], None]) -> None:
        super().__init__()
        self.setObjectName("drop")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._on_click = on_click
        layout = QHBoxLayout(self)
        layout.setContentsMargins(GAP, SPACE, GAP, SPACE)
        self.text = label("dropText")
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.text)

    def show_text(self, text: str) -> None:
        self.text.setText(f"↓  {text}")

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802 -- Qt's name
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_click()
        super().mouseReleaseEvent(event)
