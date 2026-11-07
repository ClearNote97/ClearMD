"""What the presenter's ``View`` calls do to the controls: show the state, the plan, the progress
and the result, switch the page, apply the theme and the language."""

from clearmd.frontend.design.palette import DARK, LIGHT, PALETTES
from clearmd.frontend.flet.visuals.theme import theme, theme_mode
from clearmd.frontend.flet.window import controls
from clearmd.frontend.flet.window.dialog_host import DialogHost
from clearmd.frontend.flet.window.focus import Focus
from clearmd.frontend.flet.window.frame import Frame
from clearmd.frontend.flet.window.page_port import PagePort
from clearmd.frontend.flet.window.primary_button import PrimaryButton
from clearmd.frontend.flet.window.shown import Shown
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
from clearmd.i18n import Catalog


class FletView:
    def __init__(
        self,
        page: PagePort,
        shown: Shown,
        presenter: Presenter,
        dialogs: DialogHost,
        primary_button: PrimaryButton,
        frame: Frame,
        focus: Focus,
    ) -> None:
        self._focus = focus
        self._page = page
        self._shown = shown
        self._presenter = presenter
        self._dialogs = dialogs
        self._primary_button = primary_button
        self._frame = frame
        self._rail, self._surface, self._actions = frame.rail, frame.surface, frame.actions
        self._main, self._review = frame.main, frame.review
        self._converting, self._results = frame.converting, frame.results

    def show_state(self, state: StateView) -> None:
        previous = self._shown.state
        self._shown.state = state
        if state.state is not AppState.ANALYZING:
            self._shown.scan = None
        page_changed = previous is not None and previous.page != state.page
        if page_changed:
            self._frame.message.value = ""  # a message belongs to the page it was given on
            self._primary_button.page_shown()
        converting = state.state is AppState.CONVERTING
        if converting and (previous is None or previous.state is not AppState.CONVERTING):
            self._converting.clear()
        elif state.state is AppState.WAITING_DECISION:
            self._show_ready()
        home = state.page == HOME  # the start screen: its tiles, no action bar (feature 023)
        self._frame.home.control.visible = home
        for number, page in enumerate(self._frame.pages, start=1):
            page.visible = number == state.page
        self._rail.show_page(state.page)
        self._rail.home.disabled = state.state in WORKING
        self._actions.show(state.primary)
        self._actions.control.visible = not home
        if page_changed:
            self._primary_button.pause()
        self._show_secondary(state)
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
            SecondaryKind.AGAIN: self._dialogs.convert_more,
        }
        command = commands.get(second.kind)
        self._actions.show_secondary(second.text or None, command, strong=second.strong)

    def _show_ready(self) -> None:
        count = ready_line(self._shown.catalog, self._shown.last_plan)
        if count is not None:
            self._converting.show_ready(count, str(self._main.output_label.value or ""))

    def show_inputs(self, rows: tuple[InputRow, ...]) -> None:
        self._main.show_inputs(rows)
        self._focus.watch(self._main.inputs.list)  # the rows' boxes are new

    def show_output_choice(self, choice: OutputChoice) -> None:
        self._main.show_output_choice(choice)
        if self._converting.dimmed:  # the waiting card says where results will go (014)
            self._converting.ready_where.value = self._main.output_label.value

    def show_scan(self, text: str) -> None:
        self._shown.scan = text
        self._header()

    def show_plan(self, plan: PlanView) -> None:
        self._shown.last_plan = plan
        self._review.show(plan)

    def show_progress(self, progress: ProgressView) -> None:
        self._shown.last_progress = progress
        self._converting.show(progress)

    def show_result(self, result: ResultView) -> None:
        self._shown.last_result = result
        self._results.show(result)

    def forget_work(self) -> None:
        self._shown.last_plan = None
        self._shown.last_result = None
        self._review.forget()
        self._converting.forget(str(self._main.output_label.value or ""))
        self._results.forget()

    def show_message(self, text: str) -> None:
        self._frame.message.value = text

    def apply_theme(self, name: str) -> None:
        """The two themes are always the page's; the mode says which one is on screen."""
        self._shown.palette = PALETTES.get(name, LIGHT)
        self._page.set_theme(theme(LIGHT), theme(DARK), theme_mode(self._shown.palette))

    def apply_language(self, catalog: Catalog) -> None:
        self._shown.catalog = catalog
        self._page.set_title(catalog.text("gui.app.title"))
        self._rail.apply_language(catalog)
        for view in (self._frame.home, self._main, self._review, self._converting, self._results):
            view.apply_language(catalog)
        self._header()

    def _header(self) -> None:
        if self._shown.catalog is None or self._shown.state is None:
            return
        header = header_of(self._shown.catalog, self._shown.state, self._shown.scan)
        self._surface.show_header(  # the eyebrow in capitals: the draft's own look (as Qt)
            eyebrow=header.eyebrow.upper(), title=header.title, subtitle=header.subtitle
        )
