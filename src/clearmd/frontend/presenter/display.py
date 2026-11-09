"""The push to the view: the state, the inputs, the output choice and the progress."""

from collections.abc import Callable

from clearmd.frontend.presenter.models import Primary, StateView
from clearmd.frontend.presenter.ports import View
from clearmd.frontend.presenter.screens.choose import input_rows, output_choice
from clearmd.frontend.presenter.screens.convert import progress_view
from clearmd.frontend.presenter.screens.primary import primary_of
from clearmd.frontend.presenter.screens.results import result_folders
from clearmd.frontend.presenter.session import Session
from clearmd.frontend.presenter.state import AppState, enabled_actions, step_of


class Display:
    def __init__(self, view: View, session: Session, clock: Callable[[], float]) -> None:
        self.view = view
        self._session = session
        self._clock = clock

    def primary(self) -> Primary:
        s = self._session
        return primary_of(s.catalog, s.page, s.state, s.inputs, s.plan, s.report, s.tool)

    def set_state(self, state: AppState) -> None:
        s = self._session
        s.state = state
        plan = s.plan
        enabled = enabled_actions(
            state,
            has_inputs=bool(s.inputs),
            can_confirm=bool(plan and plan.conversions),
            has_results=bool(result_folders(s.report)),
        )
        label = s.catalog.text(f"gui.state.{state.value}")
        view = StateView(state, label, enabled, step_of(state), s.page, self.primary(), s.tool)
        self.view.show_state(view)

    def show_inputs(self) -> None:
        self.view.show_inputs(input_rows(self._session.inputs, self._session.tool))

    def show_output(self) -> None:
        s = self._session
        choice = output_choice(s.catalog, s.output_folder, s.settings, s.tool)
        self.view.show_output_choice(choice)

    def show_progress(self) -> None:
        s = self._session
        if s.current is None:
            return
        elapsed = self._clock() - s.started_at
        self.view.show_progress(progress_view(s.catalog, s.current, s.done, elapsed, s.pages))
