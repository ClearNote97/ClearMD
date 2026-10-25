"""Time left for a batch, corrected with the speed measured while it runs (AC-40)."""

from collections.abc import Iterable


class TimeLeft:
    """Estimates start from the benchmark's speeds and follow the real ones.

    Each file adds a fixed overhead (sending it to the worker and back), so a tiny file whose time
    is all overhead does not distort the correction; the correction is also bounded to 0.2x-5x.
    """

    PER_FILE_OVERHEAD = 0.05
    MIN_FACTOR = 0.2
    MAX_FACTOR = 5.0

    def __init__(self, *, startup_seconds: float) -> None:
        self._startup = startup_seconds
        self._estimated = 0.0
        self._measured = 0.0
        self._finished = 0

    def record(self, *, estimated: float, measured: float) -> None:
        self._estimated += estimated + self.PER_FILE_OVERHEAD
        self._measured += measured
        self._finished += 1

    @property
    def factor(self) -> float:
        if not self._finished or self._estimated <= 0:
            return 1.0
        return min(max(self._measured / self._estimated, self.MIN_FACTOR), self.MAX_FACTOR)

    def seconds_left(self, pending_costs: Iterable[float]) -> float:
        pending = [cost + self.PER_FILE_OVERHEAD for cost in pending_costs]
        if not pending:
            return 0.0
        start_up = self._startup if not self._finished else 0.0
        return start_up + sum(pending) * self.factor
