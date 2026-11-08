"""Moving between the pages (ADR-0029): opening a step or Home, and each page's primary action."""

from clearmd.frontend.presenter.display import Display
from clearmd.frontend.presenter.intents.analysis import Analysis
from clearmd.frontend.presenter.intents.conversion import Conversion
from clearmd.frontend.presenter.intents.reset import editable
from clearmd.frontend.presenter.intents.results import Results
from clearmd.frontend.presenter.intents.tools import Tools
from clearmd.frontend.presenter.session import Session
from clearmd.frontend.presenter.state import HOME, AppState


class Navigation:
    def __init__(
        self,
        session: Session,
        display: Display,
        tools: Tools,
        analysis: Analysis,
        conversion: Conversion,
        results: Results,
    ) -> None:
        self._session = session
        self._display = display
        self._tools = tools
        self._analysis = analysis
        self._conversion = conversion
        self._results = results

    def go_to(self, page: int) -> None:
        """Show a step (0: Home, the start screen); only what is on screen changes."""
        if page == HOME:
            self._tools.go_home()
        elif 1 <= page <= 4:
            self._session.page = page
            self._display.set_state(self._session.state)

    def press_primary(self, overwrite: bool | str | None = None) -> None:
        """The page's primary action: Next, Next, Convert, Open results folder."""
        s = self._session
        if not self._display.primary().enabled:
            return
        if s.page == 1:
            if s.state is AppState.WAITING_DECISION:
                self.go_to(2)
            else:
                editable(s, self._display)  # after a batch: a new plan (007, N-1)
                self._analysis.analyze()
        elif s.page == 2:
            self.go_to(3)
        elif s.page == 3:
            self._conversion.confirm(overwrite)
        else:
            self._results.open_results()
