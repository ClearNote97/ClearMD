"""The PySide6 GUI (feature 016, ADR-0038): the same window as the ttk one, drawn by Qt.

``PySideApp`` implements the presenter's ``View``, as ``TtkApp`` does: every text and state comes
from the presenter (the same one, unchanged); the window only lays it out and forwards the user's
intents (buttons, keys, dropped files). Work comes back from the worker thread through a signal:
Qt queues it to the UI thread.
"""

import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import (
    QCloseEvent,
    QDragEnterEvent,
    QDropEvent,
    QFont,
    QKeySequence,
    QResizeEvent,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import clearmd.frontend.launch as launch
from clearmd.backend.schemas.formats import EXTENSIONS
from clearmd.frontend.design.metrics import (
    COMPACT_BELOW,
    GAP,
    MIN_HEIGHT,
    MIN_WIDTH,
    SHORT_BELOW,
    SPACE,
    START_HEIGHT,
    START_WIDTH,
)
from clearmd.frontend.design.palette import LIGHT, PALETTES, Palette
from clearmd.frontend.design.typography import BODY
from clearmd.frontend.presenter import Action, AppState, Presenter
from clearmd.frontend.presenter.chrome import close_policy, primary_gate
from clearmd.frontend.presenter.chrome.header import header_of
from clearmd.frontend.presenter.chrome.secondary import SecondaryKind, ready_line, secondary_of
from clearmd.frontend.presenter.models import (
    InputRow,
    OutputChoice,
    PlanView,
    ProgressView,
    ResultView,
    StateView,
)
from clearmd.frontend.presenter.ports import Backend
from clearmd.frontend.presenter.state import STEPS
from clearmd.frontend.pyside.dialogs import (
    Dialog,
    HelpDialog,
    KeepInputsDialog,
    SettingsDialog,
    WelcomeDialog,
)
from clearmd.frontend.pyside.pages import ChoosePage, ConvertPage, ResultsPage, ReviewPage
from clearmd.frontend.pyside.style import stylesheet
from clearmd.frontend.pyside.widgets import ActionBar, Ground, Rail, app_icon, label
from clearmd.i18n import Catalog


def application() -> QApplication:
    """The one QApplication of the process, made once; its font is the system's at 14 px."""
    existing = QApplication.instance()
    if isinstance(existing, QApplication):
        return existing
    app = QApplication(sys.argv[:1])
    app.setApplicationName("ClearMD")
    app.setWindowIcon(app_icon())
    font = QFont(app.font())
    font.setPixelSize(BODY)
    app.setFont(font)
    return app


class _Bridge(QObject):
    """From any thread to the UI thread: a queued signal, then a timer for the delay."""

    later = Signal(int, object)

    def __init__(self) -> None:
        super().__init__()
        self.later.connect(self._schedule, Qt.ConnectionType.QueuedConnection)
        self.closed = False

    def _schedule(self, milliseconds: int, callback: Callable[[], None]) -> None:
        if not self.closed:
            QTimer.singleShot(milliseconds, self, lambda: self._run(callback))

    def _run(self, callback: Callable[[], None]) -> None:
        if not self.closed:
            callback()


class PySideApp(QWidget):
    """The window, and the presenter's view."""

    def __init__(self, backend: Backend | None = None) -> None:
        application()
        super().__init__()
        self.setObjectName("window")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setWindowIcon(app_icon())
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.resize(START_WIDTH, START_HEIGHT)
        self.setAcceptDrops(True)
        self._bridge = _Bridge()
        self.palette_: Palette = LIGHT
        self.catalog: Catalog | None = None
        self.state: StateView | None = None
        self.last_plan: PlanView | None = None
        self.last_progress: ProgressView | None = None
        self.last_result: ResultView | None = None
        self._scan: str | None = None
        self.dialog: Dialog | None = None  # the open dialog: one at a time
        self._closing_since: float | None = None
        self._closed = False
        self._page_shown_at = 0.0
        self._unpause = QTimer(self)
        self._unpause.setSingleShot(True)
        self._unpause.timeout.connect(self._end_pause)
        self._build()
        self.presenter = Presenter(self, backend)
        self.rail.show_version(self.presenter.version)

    # --- Building ------------------------------------------------------------------------------

    def _build(self) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(GAP, GAP, 0, GAP)
        outer.setSpacing(0)
        self.rail = Rail(
            on_step=lambda page: self.presenter.go_to(page),
            on_settings=self.show_settings,
            on_help=self.show_help,
        )
        outer.addWidget(self.rail)
        self.ground = Ground()
        outer.addWidget(self.ground, 1)

        panel = QFrame()
        panel.setObjectName("panel")
        self.ground.body.addWidget(panel, 1)
        inside = QVBoxLayout(panel)
        inside.setContentsMargins(GAP, GAP, GAP, GAP)
        inside.setSpacing(SPACE)
        self.stack = QStackedWidget()
        inside.addWidget(self.stack, 1)
        self.message = label("message", wrap=True)
        inside.addWidget(self.message)
        self.bar = ActionBar(on_primary=self._primary)
        inside.addWidget(self.bar)

        self.main = ChoosePage(
            on_add_files=self.add_files,
            on_add_folder=self.add_folder,
            on_remove=lambda paths: self.presenter.remove_inputs(paths),
            on_clear=lambda: self.presenter.clear_inputs(),
            on_next_to=lambda: self.presenter.choose_output_next_to(),
            on_pick_folder=self.pick_output_folder,
            on_summary=lambda value: self.presenter.choose_summary_format(value),
            on_images=lambda value: self.presenter.choose_images(value),
        )
        self.review = ReviewPage()
        self.converting = ConvertPage()
        self.results = ResultsPage()
        self.pages = (self.main, self.review, self.converting, self.results)
        for page in self.pages:
            self.stack.addWidget(page)

        for number in range(1, len(STEPS) + 1):  # the rail by keyboard
            shortcut = QShortcut(QKeySequence(f"Ctrl+{number}"), self)
            shortcut.activated.connect(lambda n=number: self.presenter.go_to(n))
        for key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            enter = QShortcut(QKeySequence(key), self)
            enter.setAutoRepeat(False)  # held down: one press, whatever the page (F-1)
            enter.activated.connect(self._primary)
        delete = QShortcut(QKeySequence(Qt.Key.Key_Delete), self.main.inputs.tree)
        delete.setContext(Qt.ShortcutContext.WidgetShortcut)
        delete.activated.connect(self.main.remove.click)

    # --- Intents ---------------------------------------------------------------------------------

    def _allowed(self, action: Action) -> bool:
        return self.state is None or action in self.state.enabled

    def add_files(self) -> None:
        if not self._allowed(Action.ADD):
            return
        catalog = self._catalog()
        patterns = " ".join(f"*{extension}" for extension in sorted(EXTENSIONS))
        chosen, _filter = QFileDialog.getOpenFileNames(
            self,
            catalog.text("gui.main.pick_files_title"),
            "",
            f"{catalog.text('gui.main.documents')} ({patterns});;* (*)",
        )
        if chosen:
            self.presenter.add_paths([Path(path) for path in chosen])

    def add_folder(self) -> None:
        if not self._allowed(Action.ADD):
            return
        chosen = QFileDialog.getExistingDirectory(
            self, self._catalog().text("gui.main.pick_folder_title")
        )
        if chosen:
            self.presenter.add_paths([Path(chosen)])

    def pick_output_folder(self) -> None:
        if not self._allowed(Action.CHOOSE_OUTPUT):
            return
        suggestion = self.presenter.settings.last_output_folder or ""
        chosen = QFileDialog.getExistingDirectory(
            self, self._catalog().text("gui.main.pick_output_title"), suggestion
        )
        if chosen:
            self.presenter.choose_output_folder(Path(chosen))
        else:  # cancelled: the radio buttons show the choice as it was
            current = self.presenter.output_folder
            (self.main.in_folder if current is not None else self.main.next_to).setChecked(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802 -- Qt's name
        if event.mimeData().hasUrls() and self._allowed(Action.ADD):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802 -- Qt's name
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        if paths and self._allowed(Action.ADD):
            event.acceptProposedAction()
            self.presenter.add_paths(paths)

    def _primary(self) -> None:
        """The page's primary action, from its button or Enter (UX §6, ADR-0029). Right after the
        page changes it waits a moment, shown disabled: a double click must not run Next and
        Convert past a page the user did not see (security audit of 007, F-1)."""
        if self.dialog is not None:
            return
        if not primary_gate.gate_open(self._page_shown_at, time.monotonic()):
            return
        self.presenter.press_primary(self.review.overwrite_answer())

    def _pause_primary(self) -> None:
        pause = primary_gate.pause_milliseconds()
        if pause == 0 or not self.bar.primary.isEnabled():
            return
        self.bar.primary.setEnabled(False)
        self._unpause.start(pause)

    def _end_pause(self) -> None:
        if self.state is not None:
            self.bar.show(self.state.primary)

    def convert_more(self) -> None:
        """Asked every time: keep the chosen files, or start empty (feature 007)."""
        if self.dialog is None:
            self._open(
                KeepInputsDialog(
                    self,
                    self._catalog(),
                    on_answer=lambda keep: self.presenter.convert_more(keep=keep),
                    on_close=self._dialog_closed,
                )
            )

    def show_help(self) -> None:
        """The "?" window: always available (UX §4)."""
        if self.dialog is None:
            self._open(
                HelpDialog(
                    self, self._catalog(), self._dialog_closed, version=self.presenter.version
                )
            )

    def show_settings(self) -> None:
        if self.dialog is not None or not self._allowed(Action.SETTINGS) or self.state is None:
            return
        self._open(
            SettingsDialog(
                self,
                self._catalog(),
                self.presenter.settings,
                on_save=self.presenter.save_settings,
                on_close=self._dialog_closed,
            )
        )

    def _welcome(self, steps: tuple[str, ...]) -> None:
        if self.dialog is not None:
            return

        def done(show_again: bool) -> None:
            self._dialog_closed()
            self.presenter.dismiss_welcome(show_again=show_again)

        self._open(WelcomeDialog(self, self._catalog(), steps, done))

    def _open(self, dialog: Dialog) -> None:
        self.dialog = dialog
        dialog.open()  # modal, without a nested event loop

    def _dialog_closed(self) -> None:
        self.dialog = None

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 -- Qt's name
        super().resizeEvent(event)
        self.rail.set_compact(self.width() < COMPACT_BELOW)
        self.main.set_short(self.height() < SHORT_BELOW)

    # --- Closing ---------------------------------------------------------------------------------

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 -- Qt's name
        """Closing while converting cancels, hides the window and waits for the batch to end, so
        the summary of what was done is still written; then the window closes."""
        if self._closed:
            event.accept()
            return
        event.ignore()
        self.close_window()

    def close_window(self) -> None:
        if self._closing_since is not None or self._closed:
            return
        if self.dialog is not None:
            self.dialog.close_dialog()  # its answer counts ("Don't show again")
        self.presenter.shutdown()
        step = close_policy.on_close(self.state.state if self.state is not None else None)
        if step is close_policy.CloseStep.CANCEL_AND_WAIT:
            self._closing_since = time.monotonic()
            self.presenter.cancel()
            self.hide()
            QTimer.singleShot(close_policy.CLOSE_POLL_MS, self._close_when_done)
            return
        if step is close_policy.CloseStep.CANCEL_THEN_NOW:
            self.presenter.cancel()
        self._destroy()

    def _close_when_done(self) -> None:
        waited = time.monotonic() - (self._closing_since or 0.0)
        if close_policy.keep_waiting(self.state.state if self.state is not None else None, waited):
            QTimer.singleShot(close_policy.CLOSE_POLL_MS, self._close_when_done)
            return
        self._destroy()

    def _destroy(self) -> None:
        self._bridge.closed = True
        self._unpause.stop()
        self._closed = True
        self.close()

    @property
    def closed(self) -> bool:
        return self._closed

    # --- The View the presenter draws on ---------------------------------------------------------

    def after(self, milliseconds: int, callback: Callable[[], None]) -> None:
        self._bridge.later.emit(milliseconds, callback)

    def show_state(self, state: StateView) -> None:
        previous = self.state
        self.state = state
        if state.state is not AppState.ANALYZING:
            self._scan = None
        page_changed = previous is not None and previous.page != state.page
        if page_changed:
            self.message.setText("")  # a message belongs to the page it was given on
            self._page_shown_at = time.monotonic()
        converting = state.state is AppState.CONVERTING
        if converting and (previous is None or previous.state is not AppState.CONVERTING):
            self.converting.clear()
        elif state.state is AppState.WAITING_DECISION:
            self._show_ready()
        self.stack.setCurrentIndex(state.page - 1)
        self.rail.show_page(state.page)
        self.bar.show(state.primary)
        if page_changed:
            self._pause_primary()
        self._show_secondary(state)
        self._header()
        main = self.main
        for widget, action in (
            (main.add_files, Action.ADD),
            (main.add_folder, Action.ADD),
            (main.drop_zone, Action.ADD),
            (main.remove, Action.REMOVE),
            (main.clear, Action.REMOVE),
            *((choice, Action.CHOOSE_OUTPUT) for choice in main.choice_buttons),
            (self.rail.settings, Action.SETTINGS),
            (self.rail.help, Action.HELP),
        ):
            widget.setEnabled(action in state.enabled)

    def _show_secondary(self, state: StateView) -> None:
        """Back on Review and Convert, Cancel while working, Convert more on Results."""
        second = secondary_of(self._catalog(), state, has_result=self.last_result is not None)
        commands = {
            SecondaryKind.CANCEL: self.presenter.cancel,
            SecondaryKind.BACK: lambda: self.presenter.go_to(second.back_to),
            SecondaryKind.AGAIN: self.convert_more,
        }
        command = commands.get(second.kind)
        self.bar.show_secondary(second.text or None, command, strong=second.strong)

    def _show_ready(self) -> None:
        count = ready_line(self.catalog, self.last_plan)
        if count is not None:
            self.converting.show_ready(count, self.main.output_label.text())

    def show_inputs(self, rows: tuple[InputRow, ...]) -> None:
        self.main.show_inputs(rows)

    def show_output_choice(self, choice: OutputChoice) -> None:
        self.main.show_output_choice(choice)
        if self.converting.dimmed:  # the waiting card says where results will go (014)
            self.converting.ready_where.setText(self.main.output_label.text())

    def show_scan(self, text: str) -> None:
        self._scan = text
        self._header()

    def show_plan(self, plan: PlanView) -> None:
        self.last_plan = plan
        self.review.show(plan)

    def show_progress(self, progress: ProgressView) -> None:
        self.last_progress = progress
        self.converting.show(progress)

    def show_result(self, result: ResultView) -> None:
        self.last_result = result
        self.results.show(result)

    def forget_work(self) -> None:
        self.last_plan = None
        self.last_result = None
        self.review.forget()
        self.converting.forget(self.main.output_label.text())
        self.results.forget()

    def show_message(self, text: str) -> None:
        self.message.setText(text)

    def show_welcome(self, steps: tuple[str, ...]) -> None:
        # Once the window is on screen: the presenter asks for it while starting.
        self.after(0, lambda: self._welcome(steps))

    def apply_theme(self, theme: str) -> None:
        self.palette_ = PALETTES.get(theme, LIGHT)
        self.setStyleSheet(stylesheet(self.palette_))
        self.rail.apply_palette(self.palette_)
        self.ground.apply_palette(self.palette_)
        for page in self.pages:
            page.apply_palette(self.palette_)

    def apply_language(self, catalog: Catalog) -> None:
        self.catalog = catalog
        self.setWindowTitle(catalog.text("gui.app.title"))
        self.rail.apply_language(catalog)
        for page in self.pages:
            page.apply_language(catalog)
        self._header()

    def _header(self) -> None:
        if self.catalog is None or self.state is None:
            return
        header = header_of(self.catalog, self.state, self._scan)
        self.ground.show_header(  # Qt's eyebrow in capitals: the draft's own look (P0 list)
            eyebrow=header.eyebrow.upper(), title=header.title, subtitle=header.subtitle
        )

    def _catalog(self) -> Catalog:
        if self.catalog is None:
            raise RuntimeError("the presenter has not started")
        return self.catalog

    # --- Running ---------------------------------------------------------------------------------

    def start(self) -> None:
        self.presenter.start()
        self.show()
        self.main.add_files.setFocus()  # the first thing to do; not a step of the rail


def main(argv: Sequence[str] | None = None) -> int:
    """``clearmd-pyside``: the window, until it is closed. ``--smoke`` opens it and closes it
    after a few seconds: CI checks that the executable starts (its data, its toolkit)."""
    import multiprocessing

    multiprocessing.freeze_support()  # a no-op unless running as a packaged executable
    arguments = sys.argv[1:] if argv is None else list(argv)
    app = application()
    window = PySideApp()
    window.start()
    if launch.is_smoke(arguments):
        QTimer.singleShot(launch.SMOKE_SECONDS * 1000, window.close_window)
    return app.exec()
