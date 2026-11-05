"""Closing the window (feature 005, AC-10): while converting, the batch is cancelled and the
window waits for it to end, so the summary of what was done is still written; then it closes.
A module of its own: every GUI's closing follows it."""

from enum import StrEnum

from clearmd.frontend.presenter.state import AppState

CLOSE_POLL_MS = 50
CLOSE_WAIT_SECONDS = 60  # closing while converting: at most this long for the batch to stop


class CloseStep(StrEnum):
    NOW = "now"  # close at once
    CANCEL_THEN_NOW = "cancel_then_now"  # an analysis: drop it, then close
    CANCEL_AND_WAIT = "cancel_and_wait"  # a batch: cancel, hide the window, wait for its end


def on_close(state: AppState | None) -> CloseStep:
    if state is AppState.CONVERTING:
        return CloseStep.CANCEL_AND_WAIT
    if state is AppState.ANALYZING:
        return CloseStep.CANCEL_THEN_NOW
    return CloseStep.NOW


def keep_waiting(state: AppState | None, waited: float) -> bool:
    """Whether a window closed while converting goes on waiting for the batch to end."""
    return state is AppState.CONVERTING and waited < CLOSE_WAIT_SECONDS
