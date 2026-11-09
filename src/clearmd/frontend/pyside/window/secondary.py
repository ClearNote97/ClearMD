"""The action bar's secondary button for a state (ADR-0029): Back on Review and Convert, Cancel
while working, "What Next?" on Results. A module of its own: which command goes with which kind,
apart from what the view does with the rest of the state."""

from collections.abc import Callable

from clearmd.frontend.presenter import Presenter
from clearmd.frontend.presenter.chrome.secondary import SecondaryKind, secondary_of
from clearmd.frontend.presenter.models import StateView
from clearmd.frontend.pyside.components.action_bar import ActionBar
from clearmd.frontend.pyside.window.shown import Shown


def show_secondary(
    actions: ActionBar,
    shown: Shown,
    state: StateView,
    presenter: Presenter,
    what_next: Callable[[], None],
) -> None:
    second = secondary_of(shown.need_catalog(), state, has_result=shown.last_result is not None)
    commands = {
        SecondaryKind.CANCEL: presenter.cancel,
        SecondaryKind.BACK: lambda: presenter.go_to(second.back_to),
        SecondaryKind.AGAIN: what_next,
    }
    actions.show_secondary(second.text or None, commands.get(second.kind), strong=second.strong)
