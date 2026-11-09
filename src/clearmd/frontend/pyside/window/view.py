"""What the presenter's ``View`` calls do to the widgets: show the state, the plan, the progress and
the result, switch the page (the start screen is page 0), apply the theme and the language."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from clearmd.frontend.design.palette import LIGHT, PALETTES
from clearmd.frontend.presenter import AppState, Presenter
from clearmd.frontend.presenter.chrome.header import header_of
from clearmd.frontend.presenter.chrome.secondary import ready_line
from clearmd.frontend.presenter.models import (
    InputRow,
    OutputChoice,
    PlanView,
    ProgressView,
    ResultView,
    StateView,
)
from clearmd.frontend.presenter.state import HOME, WORKING
from clearmd.frontend.pyside.visuals.stylesheet import stylesheet
from clearmd.frontend.pyside.window import controls
from clearmd.frontend.pyside.window.dialog_host import DialogHost
from clearmd.frontend.pyside.window.frame import Frame
from clearmd.frontend.pyside.window.note import Note
from clearmd.frontend.pyside.window.offer import offer_of
from clearmd.frontend.pyside.window.primary_button import PrimaryButton
from clearmd.frontend.pyside.window.secondary import show_secondary
from clearmd.frontend.pyside.window.shown import Shown
from clearmd.i18n import Catalog


class PySideView:
    def __init__(
        self,
        window: QWidget,
        shown: Shown,
        presenter: Presenter,
        dialogs: DialogHost,
        primary_button: PrimaryButton,
        frame: Frame,
    ) -> None:
        self._window = window
        self._shown = shown
        self._presenter = presenter
        self._dialogs = dialogs
        self._primary_button = primary_button
        self._rail = frame.rail
        self._surface = frame.surface
        self._stack = frame.stack
        self._actions = frame.actions
        self._note = Note(frame.message, frame.details, frame.undo)
        self._home = frame.home
        self._panel = frame.panel
        self._main = frame.main
        self._review = frame.review
        self._converting = frame.converting
        self._results = frame.results

    def show_state(self, state: StateView) -> None:
        previous = self._shown.state
        self._shown.state = state
        if state.state is not AppState.ANALYZING:
            self._shown.scan = None
        page_changed = previous is not None and previous.page != state.page
        if page_changed:
            self.show_message("")  # a message belongs to the page it was given on
            self._primary_button.page_shown()
        converting = state.state is AppState.CONVERTING
        if converting and (previous is None or previous.state is not AppState.CONVERTING):
            self._converting.clear()
        elif state.state is AppState.WAITING_DECISION:
            self._show_ready()
        self._stack.setCurrentIndex(state.page)
        self._rail.show_page(state.page)
        self._actions.show(state.primary)
        self._actions.setVisible(state.page != HOME)  # the start screen has no primary action
        if page_changed:
            self._primary_button.pause()
            self.rest_focus()
        show_secondary(self._actions, self._shown, state, self._presenter, self._dialogs.what_next)
        self._show_offer()
        self._header()
        controls.apply_enabled(
            state.enabled, self._main, self._rail, working=state.state in WORKING
        )

    def rest_focus(self) -> None:
        """A page opens with no button looking pressed or focused (032): the keyboard rests on
        the page's panel; Tab goes on to its first control."""
        self._panel.setFocus(Qt.FocusReason.OtherFocusReason)

    def _show_offer(self) -> None:
        self._actions.show_offer(offer_of(self._shown))

    def _show_ready(self) -> None:
        count = ready_line(  # with the decision about existing results taken (035, AC-08)
            self._shown.catalog,
            self._shown.last_plan,
            self._presenter.settings.on_existing_output,
            self._review.overwrite_answer(),
        )
        if count is not None:
            self._converting.show_ready(count, self._main.output_label.text())

    def show_inputs(self, rows: tuple[InputRow, ...]) -> None:
        self._main.show_inputs(rows)

    def show_output_choice(self, choice: OutputChoice) -> None:
        self._main.show_output_choice(choice)
        if self._converting.dimmed:  # the waiting card says where results will go (014)
            self._converting.ready_where.setText(self._main.output_label.text())

    def show_scan(self, text: str) -> None:
        self._shown.scan = text
        self._header()

    def show_plan(self, plan: PlanView) -> None:
        self._shown.last_plan = plan
        self._review.show(plan)
        self._show_offer()

    def show_progress(self, progress: ProgressView) -> None:
        self._shown.last_progress = progress
        self._converting.show(progress)

    def show_result(self, result: ResultView) -> None:
        self._shown.last_result = result
        self._results.show(result)
        self._show_offer()

    def forget_work(self) -> None:
        self._shown.last_plan = None
        self._shown.last_result = None
        self._review.forget()
        self._converting.forget(self._main.output_label.text())
        self._results.forget()
        self._note.forget()
        self._show_offer()

    def show_message(self, text: str) -> None:
        self._note.show_message(text)

    def show_details_button(self, text: str | None) -> None:
        self._note.show_details_button(text)

    def show_undo(self, text: str | None) -> None:
        self._note.show_undo(text)

    def apply_theme(self, theme: str) -> None:
        self._shown.palette = PALETTES.get(theme, LIGHT)
        self._window.setStyleSheet(stylesheet(self._shown.palette))
        self._rail.apply_palette(self._shown.palette)
        self._surface.apply_palette(self._shown.palette)
        for view in (self._home, self._main, self._review, self._results):
            view.apply_palette(self._shown.palette)

    def apply_language(self, catalog: Catalog) -> None:
        self._shown.catalog = catalog
        self._note.apply_language(catalog)
        self._dialogs.apply_language(catalog)
        self._window.setWindowTitle(catalog.text("gui.app.title"))
        self._rail.apply_language(catalog)
        for view in (self._home, self._main, self._review, self._converting, self._results):
            view.apply_language(catalog)
        self._header()

    def _header(self) -> None:
        if self._shown.catalog is None or self._shown.state is None:
            return
        header = header_of(self._shown.catalog, self._shown.state, self._shown.scan)
        problems = self._shown.state.state is AppState.FINISHED_WITH_PROBLEMS  # F3-03
        self._surface.show_header(  # Qt's eyebrow in capitals: the draft's own look (P0 list)
            eyebrow=header.eyebrow.upper(),
            title=header.title,
            subtitle=header.subtitle,
            warning=problems,
        )
