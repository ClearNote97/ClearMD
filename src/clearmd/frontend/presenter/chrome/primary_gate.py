"""The primary action's pause after a page change (security audit of 007, F-1): a double click
must not run Next and Convert past a page the user did not see. The pause is read when it is
used, so a test may change it. A module of its own: every GUI's primary button reads it."""

PRIMARY_PAUSE_SECONDS = 0.5  # after a page change, before its primary action counts


def gate_open(page_shown_at: float, now: float) -> bool:
    """Whether a press at ``now`` counts, the page having changed at ``page_shown_at``."""
    return now - page_shown_at >= PRIMARY_PAUSE_SECONDS


def pause_milliseconds() -> int:
    """How long the button stays disabled after a page change (0: no pause)."""
    return int(PRIMARY_PAUSE_SECONDS * 1000) if PRIMARY_PAUSE_SECONDS > 0 else 0
