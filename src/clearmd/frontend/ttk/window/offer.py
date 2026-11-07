""" "Split the Large PDFs" (feature 025): in the action bar, just left of the page's secondary
action (Back on Review, Convert More on Results), while Review's plan or Results' result offers
it. A module of its own: the view stays within its size."""

from clearmd.frontend.presenter import Presenter
from clearmd.frontend.ttk.components.action_bar import ActionBar
from clearmd.frontend.ttk.window.shown import Shown

REVIEW, RESULTS = 2, 4


def show_offer(actions: ActionBar, shown: Shown, presenter: Presenter) -> None:
    """The offer of the page on screen, or none; the press is resolved when it happens."""
    page = shown.state.page if shown.state is not None else 0
    offered = {REVIEW: shown.last_plan, RESULTS: shown.last_result}.get(page)
    text = offered.split_offer if offered is not None else ""
    actions.show_offer(text or None, lambda: presenter.split_large())
