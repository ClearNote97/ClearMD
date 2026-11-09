"""The ttkbootstrap window: the composition root, and the presenter's ``View`` (ADR-0026, ADR-0027).

``TtkApp`` builds the widgets and the collaborators of ``window/`` and forwards every ``View`` call
to the one that does it: every text and state comes from the presenter; the window only lays it
out and forwards the user's intents (buttons, keys, dropped files).
"""

import tkinter as tk
from collections.abc import Callable
from functools import partial
from tkinter import ttk
from typing import Any

from clearmd.frontend.design.palette import Palette
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
from clearmd.frontend.ttk.components.dialog import Dialog
from clearmd.frontend.ttk.window import controls, toolkit
from clearmd.frontend.ttk.window.closing import Closing
from clearmd.frontend.ttk.window.dialog_host import DialogHost
from clearmd.frontend.ttk.window.frame import build_frame
from clearmd.frontend.ttk.window.inputs import Inputs
from clearmd.frontend.ttk.window.pickers import Pickers
from clearmd.frontend.ttk.window.primary_button import PrimaryButton
from clearmd.frontend.ttk.window.scheduler import Scheduler
from clearmd.frontend.ttk.window.shown import Shown
from clearmd.frontend.ttk.window.view import TtkView
from clearmd.i18n import Catalog


class TtkApp:
    """The window, and the presenter's view."""

    def __init__(self, backend: Backend | None = None, *, root: tk.Tk | None = None) -> None:
        # TkinterDnD.Tk: a Tk root with drag and drop (tkinterdnd2 has no types). Without its
        # library (a Tk it was not built for), the window works with Add files / Add folder only.
        self.root: Any = root or toolkit.root_with_drop()
        self.drops = bool(getattr(self.root, "TkdndVersion", None))
        self.style, self.fonts, self.look = toolkit.prepare(self.root)
        self.shown = Shown()
        self.look.use(self.shown.palette)  # the styles exist before the widgets that use them
        self.scheduler = Scheduler(self.root)
        self.presenter = Presenter(self, backend)  # it never calls the view while it is built
        self.dialogs = DialogHost(
            self.root, self.fonts, self.presenter, self.shown, drops=self.drops
        )
        self._build()
        self.closing = Closing(
            self.root, self.presenter, self.shown, self.scheduler, self.dialogs, self.primary_button
        )
        self.rail.show_version(self.presenter.version)
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.closing.close(confirmed=False))  # 038

    def _build(self) -> None:
        self.icons = toolkit.set_icons(self.root)
        # The widgets' callbacks reach what is built after them through lambdas, resolved on use.
        frame = build_frame(
            self.root,
            self.fonts,
            self.presenter,
            self.dialogs,
            on_primary=lambda: self.primary_button.press(),
            on_add_files=lambda: self.pickers.add_files(),
            on_add_folder=lambda: self.pickers.add_folder(),
            on_pick_folder=lambda: self.pickers.pick_output_folder(),
        )
        self.rail, self.surface, self.actions = frame.rail, frame.surface, frame.actions
        self.home = frame.home  # the start screen (feature 023)
        self.main, self.review, self.message = frame.main, frame.review, frame.message
        self.converting, self.results = frame.converting, frame.results
        self.pickers = Pickers(self.root, self.presenter, self.shown, self.main.output_mode)
        self.primary_button = PrimaryButton(
            self.root, self.actions, self.review, self.presenter, self.dialogs, self.shown
        )
        self.view = TtkView(
            self.root,
            self.look,
            self.shown,
            self.presenter,
            self.dialogs,
            self.primary_button,
            frame,
        )
        self.pages = self.view.pages
        self.view.show_page(self.main)
        self.inputs = Inputs(
            self.root,
            self.presenter,
            self.shown,
            self.primary_button.press,
            self.actions.primary,
            drops=self.drops,
        )
        self.inputs.bind()
        self.root.bind(
            "<Configure>", partial(controls.fit_to_size, self.root, self.main, self.rail), add="+"
        )

    @property
    def dialog(self) -> Dialog | None:
        return self.dialogs.current

    @property
    def state(self) -> StateView | None:
        return self.shown.state

    @property
    def palette(self) -> Palette:
        return self.shown.palette

    @property
    def last_plan(self) -> PlanView | None:
        return self.shown.last_plan

    @property
    def last_result(self) -> ResultView | None:
        return self.shown.last_result

    @property
    def page(self) -> ttk.Frame | None:
        return self.shown.page

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
        """ "Copy Details" after an unexpected error; ``None`` hides it (feature 036)."""
        self.actions.show_details(label, self.presenter.copy_details)

    def copy_text(self, text: str) -> None:
        """The system clipboard (feature 036); kept by Tk until another program takes it."""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

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
        self.root.deiconify()
