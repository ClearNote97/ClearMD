"""The settings: read at the start, applied (language, theme), saved; and the welcome."""

from collections.abc import Callable
from dataclasses import replace

from clearmd.backend.schemas.settings import CHOICES, Settings
from clearmd.frontend.presenter.display import Display
from clearmd.frontend.presenter.intents.reset import editable
from clearmd.frontend.presenter.ports import Backend
from clearmd.frontend.presenter.screens.results import result_view
from clearmd.frontend.presenter.screens.review import plan_view
from clearmd.frontend.presenter.session import Session
from clearmd.frontend.presenter.state import WORKING, AppState
from clearmd.i18n import load_catalog, printable, resolve_language


def save(session: Session, display: Display, backend: Backend, settings: Settings) -> None:
    """Keep ``settings`` and write them; told if the file cannot be written."""
    session.settings = settings
    try:
        backend.save_settings(settings)
    except (OSError, ValueError):
        display.view.show_message(session.catalog.text("gui.settings.not_saved"))


class Preferences:
    def __init__(
        self,
        session: Session,
        display: Display,
        backend: Backend,
        detect_theme: Callable[[], str],
    ) -> None:
        self._session = session
        self._display = display
        self._backend = backend
        self._detect_theme = detect_theme

    def start(self) -> None:
        """Read the settings, apply the language and the theme, show the welcome if wanted."""
        s = self._session
        settings, warnings = self._backend.load_settings()
        self._apply(settings)
        self._display.show_inputs()
        self._display.show_output()
        self._display.set_state(AppState.READY)
        if warnings:  # after the first state: a view may clear its message on a step change
            lines = (
                s.catalog.text(f"settings.{warning.problem.value}", setting=warning.key)
                for warning in warnings
            )
            self._display.view.show_message("\n".join(printable(line) for line in lines))
        if s.settings.show_welcome:
            self._display.view.show_welcome(
                tuple(s.catalog.text(f"gui.welcome.step{n}") for n in (1, 2, 3))
            )

    def _apply(self, settings: Settings) -> None:
        s = self._session
        view = self._display.view
        s.settings = settings
        s.catalog = load_catalog(resolve_language(None, settings.language)).for_tool(s.tool)
        view.apply_language(s.catalog)
        theme = settings.theme if settings.theme != "system" else self._detect_theme()
        theme = theme if theme in {"light", "dark"} else "light"
        if theme != s.theme:  # redrawing the lists for nothing loses their selection
            s.theme = theme
            view.apply_theme(theme)

    def save_settings(self, settings: Settings) -> None:
        """Save and apply at once (language, theme); told if the file cannot be written."""
        s = self._session
        old = s.settings
        if (old.recursive, old.html_strategy) != (settings.recursive, settings.html_strategy):
            editable(
                s, self._display
            )  # these change what a plan holds: it is made again (007, I-1)
        self._apply(settings)
        save(s, self._display, self._backend, settings)
        self._display.show_inputs()
        self._display.show_output()
        if s.plan is not None and s.state is AppState.WAITING_DECISION:
            self._display.view.show_plan(
                plan_view(s.catalog, s.plan, s.settings.on_existing_output, s.plan_id)
            )
        if s.report is not None:  # the results, in the new language
            self._display.view.show_result(result_view(s.catalog, s.report, s.state))
        self._display.set_state(s.state)

    def choose_summary_format(self, summary_format: str) -> None:
        """Markdown, or Markdown + PDF: chosen on step 1 and remembered (ADR-0031)."""
        s = self._session
        valid = summary_format in CHOICES["summary_format"]
        if not valid or summary_format == s.settings.summary_format or s.state in WORKING:
            self._display.show_output()  # the radio buttons show the choice as it is
            return
        self.save_settings(replace(s.settings, summary_format=summary_format))

    def choose_images(self, images: str) -> None:
        """Images left out, or in a folder next to each Markdown: chosen on step 1 (ADR-0033)."""
        s = self._session
        valid = images in CHOICES["images"]
        if not valid or images == s.settings.images or s.state in WORKING:
            self._display.show_output()
            return
        self.save_settings(replace(s.settings, images=images))

    def restore_defaults(self) -> None:
        self.save_settings(Settings())

    def dismiss_welcome(self, *, show_again: bool) -> None:
        if not show_again:
            save(
                self._session,
                self._display,
                self._backend,
                replace(self._session.settings, show_welcome=False),
            )
