"""A page that scrolls rather than squeezing its cards when the window is too short for them
(feature 024: step 1 with Split's block in a window of the minimum height)."""

from PySide6.QtCore import QEvent, QObject, QSize, Qt
from PySide6.QtWidgets import QFrame, QScrollArea, QWidget


class ScrollPage(QScrollArea):
    """``page`` gets the room there is, down to its minimum height; below that, a scroll bar.
    Not Qt's resizable widget: with wrapped lines it would give the page its preferred height and
    scroll a window that has room for it."""

    def __init__(self, page: QWidget) -> None:
        super().__init__()
        self.page = page
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(page)
        page.installEventFilter(self)  # its minimum changes with what it shows

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802 -- Qt's name
        if watched is self.page and event.type() is QEvent.Type.LayoutRequest:
            self.fit()
        return super().eventFilter(watched, event)

    def viewportEvent(self, event: QEvent) -> bool:  # noqa: N802 -- Qt's name
        if event.type() is QEvent.Type.Resize:  # the window, or the scroll bar coming and going
            self.fit()
        return super().viewportEvent(event)

    def fit(self) -> None:
        room = self.viewport().size()
        layout = self.page.layout()
        needed = (  # its wrapped lines in full, at this width; the lists ask only their minimum
            layout.totalHeightForWidth(room.width())
            if layout is not None and layout.hasHeightForWidth()
            else self.page.minimumSizeHint().height()
        )
        size = QSize(room.width(), max(room.height(), needed))
        if self.page.size() != size:
            self.page.resize(size)
