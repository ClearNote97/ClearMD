"""The flet window's owner: the composition root, and the presenter's ``View`` (ADR-0038).

``FletApp`` is a plain object built on a page port (``PagePort``): flet's real page through
``FletPage``, or a test's page. It builds the collaborators of ``window/`` and forwards every
``View`` call to the one that does it: every text and state comes from the presenter; the window
only lays it out and forwards the user's intents (buttons, keys, the pickers' answers).
"""

from collections.abc import Callable

import flet as ft

from clearmd.frontend.flet.window import controls
from clearmd.frontend.flet.window.closing import Closing
from clearmd.frontend.flet.window.dialog_host import DialogHost
from clearmd.frontend.flet.window.focus import Focus
from clearmd.frontend.flet.window.frame import build_frame
from clearmd.frontend.flet.window.keys import Keys
from clearmd.frontend.flet.window.page_port import PagePort
from clearmd.frontend.flet.window.pickers import Pickers
from clearmd.frontend.flet.window.primary_button import PrimaryButton
from clearmd.frontend.flet.window.scheduler import Scheduler
from clearmd.frontend.flet.window.shown import Shown
from clearmd.frontend.flet.window.view import FletView
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
from clearmd.i18n import Catalog


class FletApp:
    """The window's owner, and the presenter's view: its controls hang from ``self.root``."""

    def __init__(self, page: PagePort, backend: Backend | None = None) -> None:
        self.page = page
        self.shown = Shown()
        self.scheduler = Scheduler(page.post)
        self.presenter = Presenter(self, backend)  # it never calls the view while it is built
        self.focus = Focus()
        self.dialogs = DialogHost(page, self.presenter, self.shown, self.focus)
        self._build()
        self.closing = Closing(
            page, self.presenter, self.shown, self.scheduler, self.dialogs, self.primary_button
        )
        self.rail.show_version(self.presenter.version)
        page.listen(
            on_key=self.keys.pressed,
            on_close=self.closing.request,  # the X: asks first while a task runs (038)
            on_resize=lambda width, _height: controls.fit_to_size(self.rail, width),
        )

    def _build(self) -> None:
        # The controls' callbacks reach what is built after them through lambdas, resolved on use.
        frame = build_frame(
            self.presenter,
            self.dialogs,
            on_primary=lambda: self.primary_button.press(),
            on_add_files=lambda: self.pickers.add_files(),
            on_add_folder=lambda: self.pickers.add_folder(),
            on_pick_folder=lambda: self.pickers.pick_output_folder(),
        )
        self.root: ft.Container = frame.root
        self.rail, self.surface, self.actions = frame.rail, frame.surface, frame.actions
        self.main, self.review, self.message = frame.main, frame.review, frame.message
        self.message_line = frame.message_line
        self.converting, self.results, self.panel = frame.converting, frame.results, frame.panel
        self.pages, self.home = frame.pages, frame.home
        self.pickers = Pickers(self.page, self.presenter, self.shown, self.main.mode)
        self.primary_button = PrimaryButton(
            self.actions, self.review, self.presenter, self.dialogs, self.shown, self.scheduler
        )
        self.view = FletView(
            self.page,
            self.shown,
            self.presenter,
            self.dialogs,
            self.primary_button,
            frame,
            self.focus,
        )
        self.keys = Keys(
            self.presenter, self.dialogs, self.primary_button.press, self.main, self.focus
        )
        self.focus.watch(self.root)

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
        # Alone in its callback (each second, each file's start): only the progress card is sent.
        self.view.show_progress(progress)
        self.page.narrow(self.converting.progress_card)

    def show_result(self, result: ResultView) -> None:
        self.view.show_result(result)

    def show_message(self, text: str) -> None:
        self.view.show_message(text)

    def show_details_button(self, label: str | None) -> None:
        """ "Copy Details" beside the message after an unexpected error; ``None`` hides it (036)."""
        self.message_line.show_details(label)

    def show_undo(self, text: str | None) -> None:
        """After Clear All: the line and "Undo" beside it; ``None`` hides both (039)."""
        self.message_line.show_undo(text, self.shown.need_catalog().text("gui.main.undo"))

    def copy_text(self, text: str) -> None:
        self.page.copy_text(text)

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
        """The presenter fills the controls, then they go to the screen at once."""
        self.presenter.start()
        self.page.mount(self.root)
