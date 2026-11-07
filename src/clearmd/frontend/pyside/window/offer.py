"""Which "Split the Large PDFs (N)" the action bar offers (feature 025): Review's from the plan,
Results' from the result; none while working or on the other pages. A module of its own: a rule
about what is shown, apart from the widgets."""

from clearmd.frontend.presenter.state import WORKING
from clearmd.frontend.pyside.window.shown import Shown


def offer_of(shown: Shown) -> str:
    state, plan, result = shown.state, shown.last_plan, shown.last_result
    if state is None or state.state in WORKING:
        return ""
    if state.page == 2 and plan is not None:
        return plan.split_offer
    if state.page == 4 and result is not None:
        return result.split_offer
    return ""
