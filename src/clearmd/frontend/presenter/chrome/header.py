"""The page's header (ADR-0027): the step counter (with the state while it is not Ready), the
step's title and its subtitle (or the scan's count while analyzing). A module of its own: every
GUI draws its header from it."""

from dataclasses import dataclass

from clearmd.frontend.presenter.models import StateView
from clearmd.frontend.presenter.state import HOME, STEPS, AppState
from clearmd.i18n import Catalog


@dataclass(frozen=True)
class Header:
    eyebrow: str
    title: str
    subtitle: str


def header_of(catalog: Catalog, state: StateView, scan: str | None) -> Header:
    """What the header says on ``state``'s page; ``scan`` replaces the subtitle while analyzing.
    Home (page 0, feature 023) has no step counter: its own title and subtitle."""
    if state.page == HOME:
        return Header("", catalog.text("gui.home.title"), catalog.text("gui.home.subtitle"))
    step = STEPS[state.page - 1]
    eyebrow = catalog.text("gui.steps.counter", step=state.page, total=len(STEPS))
    if state.state is not AppState.READY:
        eyebrow = f"{eyebrow} · {state.label}"
    return Header(
        eyebrow=eyebrow,
        title=catalog.text(f"gui.page.{step}_title"),
        subtitle=scan or catalog.text(f"gui.page.{step}_subtitle"),
    )
