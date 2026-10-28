"""The seven states of the UX contract (§1) and what the user can do in each (ADR-0026)."""

from enum import StrEnum


class AppState(StrEnum):
    READY = "ready"
    ANALYZING = "analyzing"
    WAITING_DECISION = "waiting_decision"
    CONVERTING = "converting"
    FINISHED = "finished"
    FINISHED_WITH_PROBLEMS = "finished_with_problems"
    CANCELLED = "cancelled"


class Action(StrEnum):
    """What a view can offer; each state enables some of them."""

    ADD = "add"
    REMOVE = "remove"
    CHOOSE_OUTPUT = "choose_output"
    CONVERT = "convert"
    CONFIRM = "confirm"
    BACK = "back"
    CANCEL = "cancel"
    OPEN_RESULTS = "open_results"
    SETTINGS = "settings"
    HELP = "help"


_EDITING = frozenset({Action.ADD, Action.CHOOSE_OUTPUT, Action.SETTINGS, Action.HELP})
_FINISHED = frozenset({Action.BACK, Action.OPEN_RESULTS, Action.SETTINGS, Action.HELP})


def enabled_actions(
    state: AppState, *, has_inputs: bool, can_confirm: bool, has_results: bool
) -> frozenset[Action]:
    """The actions a view enables in ``state``: Convert and Remove only with inputs, Confirm only
    with something to convert, Cancel only while working, Help always (UX §4)."""
    if state is AppState.READY:
        return _EDITING | ({Action.CONVERT, Action.REMOVE} if has_inputs else set())
    if state in {AppState.ANALYZING, AppState.CONVERTING}:
        return frozenset({Action.CANCEL, Action.HELP})
    if state is AppState.WAITING_DECISION:
        return frozenset({Action.BACK, Action.HELP} | ({Action.CONFIRM} if can_confirm else set()))
    return _FINISHED if has_results else _FINISHED - {Action.OPEN_RESULTS}
