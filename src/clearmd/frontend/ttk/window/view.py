"""What the presenter's ``View`` calls do to the widgets: show the state, the plan, the progress and
the result, switch the page (Home or a step), apply the theme and the language."""

from tkinter import ttk
from typing import Any

from clearmd.frontend.design.palette import LIGHT, PALETTES
from clearmd.frontend.presenter import AppState, Presenter
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
from clearmd.frontend.presenter.state import HOME, WORKING
from clearmd.frontend.ttk.visuals.look import Look
from clearmd.frontend.ttk.window import controls, home_chrome, offer
from clearmd.frontend.ttk.window.dialog_host import DialogHost
from clearmd.frontend.ttk.window.frame import Frame
from clearmd.frontend.ttk.window.primary_button import PrimaryButton
from clearmd.frontend.ttk.window.shown import Shown
from clearmd.i18n import Catalog


class TtkView:
    def __init__(
        self,
        root: Any,
        look: Look,
        shown: Shown,
        presenter: Presenter,
        dialogs: DialogHost,
        primary_button: PrimaryButton,
        frame: Frame,
    ) -> None:
        self._root = root
        self._look = look
        self._shown = shown
        self._presenter = presenter
        self._dialogs = dialogs
        self._primary_button = primary_button
        self._rail = frame.rail
        self._surface = frame.surface
        self._actions = frame.actions
        self._message = frame.message
        self._main = frame.main
        self._review = frame.review
        self._converting = frame.converting
        self._results = frame.results
        self._home = frame.home  # the start screen, page 0 (feature 023)
        # One page per step (ADR-0027): Choose (also while analyzing), Review, Convert, Results.
        self.pages: tuple[ttk.Frame, ...] = (
            self._main,
            self._review,
            self._converting,
            self._results,
        )

    def show_state(self, state: StateView) -> None:
        previous = self._shown.state
        self._shown.state = state
        if state.state is not AppState.ANALYZING:
            self._shown.scan = None
        if previous is not None and previous.page != state.page:
            self._message.configure(text="")  # a message belongs to the page it was given on
            self._primary_button.page_shown()
            home_chrome.calm_focus(self._root)
        converting = state.state is AppState.CONVERTING
        if converting and (previous is None or previous.state is not AppState.CONVERTING):
            self._converting.clear()
        elif state.state is AppState.WAITING_DECISION:
            self._show_ready()
        home = state.page == HOME
        self.show_page(self._home if home else self.pages[state.page - 1])
        self._rail.show_page(state.page)
        self._rail.set_home_enabled(state.state not in WORKING)
        page = self._shown.page or self._main
        home_chrome.show_bar(self._actions, self._message, page, shown=not home)
        self._actions.show(state.primary)
        if previous is not None and previous.page != state.page:
            self._primary_button.pause()
        self._show_secondary(state)
        offer.show_offer(self._actions, self._shown, self._presenter)
        self._header()
        controls.apply_enabled(state.enabled, self._main, self._rail)

    def _show_secondary(self, state: StateView) -> None:
        """Back on Review and Convert, Cancel while working, Convert more on Results."""
        second = secondary_of(
            self._shown.need_catalog(), state, has_result=self._shown.last_result is not None
        )
        commands = {
            SecondaryKind.CANCEL: self._presenter.cancel,
            SecondaryKind.BACK: lambda: self._presenter.go_to(second.back_to),
            SecondaryKind.AGAIN: self._dialogs.what_next,
        }
        command = commands.get(second.kind)
        self._actions.show_secondary(second.text or None, command, strong=second.strong)

    def _show_ready(self) -> None:
        """Convert's card before the batch: how many are ready, and where they go."""
        count = ready_line(self._shown.catalog, self._shown.last_plan)
        if count is not None:
            self._converting.show_ready(count, str(self._main.output_label.cget("text")))

    def show_inputs(self, rows: tuple[InputRow, ...]) -> None:
        self._main.show_inputs(rows)

    def show_output_choice(self, choice: OutputChoice) -> None:
        self._main.show_output_choice(choice)
        if self._converting.dimmed:  # the waiting card says where results will go (014)
            self._converting.ready_where.configure(text=str(self._main.output_label.cget("text")))

    def show_scan(self, text: str) -> None:
        self._shown.scan = text
        self._header()

    def show_plan(self, plan: PlanView) -> None:
        self._shown.last_plan = plan
        self._review.show(plan)
        offer.show_offer(self._actions, self._shown, self._presenter)

    def show_progress(self, progress: ProgressView) -> None:
        self._shown.last_progress = progress
        self._converting.show(progress)

    def show_result(self, result: ResultView) -> None:
        self._shown.last_result = result
        self._results.show(result)
        offer.show_offer(self._actions, self._shown, self._presenter)

    def show_page(self, page: ttk.Frame) -> None:
        if page is self._shown.page:
            return
        if self._shown.page is not None:
            self._shown.page.pack_forget()
        page.pack(fill="both", expand=True)
        self._shown.page = page

    def forget_work(self) -> None:
        self._shown.last_plan = None
        self._shown.last_result = None
        self._review.forget()
        self._converting.forget(str(self._main.output_label.cget("text")))
        self._results.forget()
        offer.show_offer(self._actions, self._shown, self._presenter)

    def show_message(self, text: str) -> None:
        self._message.configure(text=text)

    def apply_theme(self, theme: str) -> None:
        self._shown.palette = PALETTES.get(theme, LIGHT)
        self._look.use(self._shown.palette)
        self._root.configure(background=self._shown.palette.ground)
        self._rail.apply_palette(self._shown.palette)
        self._surface.apply_palette(self._shown.palette)
        for view in (self._home, self._main, self._review, self._results):
            view.apply_palette(self._shown.palette)

    def apply_language(self, catalog: Catalog) -> None:
        self._shown.catalog = catalog
        self._root.title(catalog.text("gui.app.title"))
        self._rail.apply_language(catalog)
        for view in (self._home, self._main, self._review, self._converting, self._results):
            view.apply_language(catalog)
        self._header()

    def _header(self) -> None:
        if self._shown.catalog is None or self._shown.state is None:
            return
        header = header_of(self._shown.catalog, self._shown.state, self._shown.scan)
        self._surface.show_header(
            eyebrow=header.eyebrow, title=header.title, subtitle=header.subtitle
        )
