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


class Tool(StrEnum):
    """What the batch does (ADR-0043): convert to Markdown, or split PDFs (feature 023)."""

    CONVERT = "convert"
    SPLIT = "split"
    MERGE = "merge"  # feature 026


HOME = 0  # the start screen: the page before step 1 (feature 023)


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
_FINISHED = frozenset({Action.BACK, Action.OPEN_RESULTS} | _EDITING)
WORKING = frozenset({AppState.ANALYZING, AppState.CONVERTING})


def enabled_actions(
    state: AppState, *, has_inputs: bool, can_confirm: bool, has_results: bool
) -> frozenset[Action]:
    """The actions a view enables in ``state``: Convert and Remove only with inputs, Confirm only
    with something to convert, Cancel only while working, Help always (UX §4). Outside the work,
    the inputs can always be edited (ADR-0029: editing drops a plan or a result)."""
    remove = {Action.REMOVE} if has_inputs else set()
    if state is AppState.READY:
        return _EDITING | remove | ({Action.CONVERT} if has_inputs else set())
    if state in WORKING:
        return frozenset({Action.CANCEL, Action.HELP})
    if state is AppState.WAITING_DECISION:
        confirm = {Action.CONFIRM} if can_confirm else set()
        return frozenset({Action.BACK} | _EDITING | remove | confirm)
    finished = _FINISHED | remove
    return finished if has_results else finished - {Action.OPEN_RESULTS}


STEPS = ("choose", "review", "convert", "results")  # the flow, as the rail shows it (ADR-0027)


def step_of(state: AppState) -> int:
    """Which of the four steps a state belongs to (1-based)."""
    if state is AppState.READY:
        return 1
    if state in {AppState.ANALYZING, AppState.WAITING_DECISION}:
        return 2
    if state is AppState.CONVERTING:
        return 3
    return 4
