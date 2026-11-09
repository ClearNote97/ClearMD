"""The Qt window's owner: the composition root, and the presenter's ``View`` (ADR-0038).

``PySideApp`` is a plain object. It owns the ``MainWindow`` widget, builds the collaborators of
``window/`` and forwards every ``View`` call to the one that does it: every text and state comes
from the presenter; the window only lays it out and forwards the user's intents (buttons, keys,
dropped files).
"""

from collections.abc import Callable

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from clearmd.frontend.presenter import Presenter
from clearmd.frontend.presenter.models import (
    InputRow,
    OutputChoice,
    PlanView,
    ProgressView,
    ResultView,
    StateView,
)
from clearmd.frontend.presenter.ports import Backend
from clearmd.frontend.pyside.window import controls, toolkit
from clearmd.frontend.pyside.window.closing import Closing
from clearmd.frontend.pyside.window.dialog_host import DialogHost
from clearmd.frontend.pyside.window.frame import build_frame
from clearmd.frontend.pyside.window.inputs import Inputs
from clearmd.frontend.pyside.window.pickers import Pickers
from clearmd.frontend.pyside.window.primary_button import PrimaryButton
from clearmd.frontend.pyside.window.qt_window import MainWindow
from clearmd.frontend.pyside.window.scheduler import Scheduler
from clearmd.frontend.pyside.window.shown import Shown
from clearmd.frontend.pyside.window.view import PySideView
from clearmd.i18n import Catalog


class PySideApp:
    """The window's owner, and the presenter's view: the Qt widget is ``self.window``."""

    def __init__(
        self, backend: Backend | None = None, *, application: QApplication | None = None
    ) -> None:
        self.application = application or toolkit.application()
        self.window = MainWindow()
        self.shown = Shown()
        self.scheduler = Scheduler()
        self.presenter = Presenter(self, backend)  # it never calls the view while it is built
        self.dialogs = DialogHost(self.window, self.presenter, self.shown)
        self._build()
        self.closing = Closing(
            self.window,
            self.presenter,
            self.shown,
            self.scheduler,
            self.dialogs,
            self.primary_button,
        )
        self.rail.show_version(self.presenter.version)
        self.window.on_close = self.closing.close_event
        self.window.on_resize = lambda width, height: controls.fit_to_size(
            self.main, self.rail, width, height
        )
        self.window.on_drag_enter = self.inputs.drag_enter
        self.window.on_drop = self.inputs.dropped

    def _build(self) -> None:
        # The widgets' callbacks reach what is built after them through lambdas, resolved on use.
        frame = build_frame(
            self.window,
            self.presenter,
            self.dialogs,
            on_primary=lambda: self.primary_button.press(),
            on_add_files=lambda: self.pickers.add_files(),
            on_add_folder=lambda: self.pickers.add_folder(),
            on_pick_folder=lambda: self.pickers.pick_output_folder(),
        )
        self.rail, self.surface, self.actions = frame.rail, frame.surface, frame.actions
        self.home, self.main = frame.home, frame.main
        self.review, self.message = frame.review, frame.message
        self.details = frame.details  # "Copy Details" (036)
        self.converting, self.results = frame.converting, frame.results
        self.pickers = Pickers(
            self.window, self.presenter, self.shown, self.main.next_to, self.main.in_folder
        )
        self.primary_button = PrimaryButton(
            self.window, self.actions, self.review, self.presenter, self.dialogs, self.shown
        )
        self.view = PySideView(
            self.window, self.shown, self.presenter, self.dialogs, self.primary_button, frame
        )
        self.inputs = Inputs(
            self.window,
            self.presenter,
            self.shown,
            self.primary_button.press,
            self.main.inputs.tree,
            self.main.remove,
        )
        self.inputs.bind()

    # --- The View the presenter draws on ---------------------------------------------------------

    def after(self, milliseconds: int, callback: Callable[[], None]) -> None:
        self.scheduler.after(milliseconds, callback)

    def show_state(self, state: StateView) -> None:
        self.view.show_state(state)

    def show_inputs(self, rows: tuple[InputRow, ...]) -> None:
        self.view.show_inputs(rows)

    def show_output_choice(self, choice: OutputChoice) -> None:
        self.view.show_output_choice(choice)

    def show_scan(self, text: str) -> None:
        self.view.show_scan(text)

    def show_plan(self, plan: PlanView) -> None:
        self.view.show_plan(plan)

    def show_progress(self, progress: ProgressView) -> None:
        self.view.show_progress(progress)

    def show_result(self, result: ResultView) -> None:
        self.view.show_result(result)

    def show_message(self, text: str) -> None:
        self.view.show_message(text)

    def show_details_button(self, label: str | None) -> None:
        self.view.show_details_button(label)

    def copy_text(self, text: str) -> None:
        QGuiApplication.clipboard().setText(text)  # "Copy Details" (036)

    def show_welcome(self, steps: tuple[str, ...]) -> None:
        # Once the window is on screen: the presenter asks for it while starting.
        self.scheduler.after(0, lambda: self.dialogs.welcome(steps))

    def forget_work(self) -> None:
        self.view.forget_work()

    def apply_theme(self, theme: str) -> None:
        self.view.apply_theme(theme)

    def apply_language(self, catalog: Catalog) -> None:
        self.view.apply_language(catalog)

    def close(self) -> None:
        self.closing.close()

    def start(self) -> None:
        self.presenter.start()
        self.window.show()
        self.view.rest_focus()  # no button looks focused when the window opens (032)
