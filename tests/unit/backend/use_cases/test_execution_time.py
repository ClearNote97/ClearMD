"""Executing a plan: time left and stopped files."""

from datetime import datetime, timedelta
from pathlib import Path

from support.execution_fakes import NOW, FakeRunner, _item, _plan, _run

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.events import BatchEvent, ConversionStarted
from clearmd.backend.schemas.models import (
    ConversionResult,
    OutcomeStatus,
    PlannedConversion,
)
from clearmd.backend.use_cases.cancel import CancelToken
from clearmd.backend.use_cases.execution import execute_plan


class StepClock:
    """Each call is ``step`` seconds after the previous one."""

    def __init__(self, step: float) -> None:
        self.step = step
        self.calls = 0

    def now(self) -> datetime:
        self.calls += 1
        return NOW + timedelta(seconds=self.calls * self.step)


def test_outcomes_carry_their_time_and_events_carry_the_time_left(tmp_path: Path) -> None:
    items = tuple(_item(tmp_path, f"{name}.pdf") for name in ("a", "b", "c"))
    events: list[BatchEvent] = []
    report = execute_plan(
        _plan(*items),
        overwrite=lambda item: True,
        runner=FakeRunner(),
        on_event=events.append,
        cancel=CancelToken(),
        clock=StepClock(2.0),
    )
    assert all(outcome.seconds > 0 for outcome in report.outcomes)
    started = [event for event in events if isinstance(event, ConversionStarted)]
    assert started[0].seconds_left is None  # nothing measured yet
    assert all(event.seconds_left is not None for event in started[1:])


class StoppingRunner(FakeRunner):
    def convert(self, item: PlannedConversion, cancel: CancelToken) -> ConversionResult:
        if item.source.stem == "slow":
            raise ConversionError(ErrorCode.TIMED_OUT, "stopped after 600 s")
        if item.source.stem == "huge":
            raise ConversionError(ErrorCode.OUT_OF_MEMORY, "worker used 4100 MiB, limit 4096 MiB")
        return super().convert(item, cancel)


def test_time_and_memory_limits_give_a_stopped_outcome(tmp_path: Path) -> None:
    items = (_item(tmp_path, "slow.pdf"), _item(tmp_path, "huge.pdf"), _item(tmp_path, "ok.pdf"))
    _, report = _run(_plan(*items), StoppingRunner())
    statuses = [(o.status, o.error) for o in report.outcomes]
    assert statuses == [
        (OutcomeStatus.STOPPED, ErrorCode.TIMED_OUT),
        (OutcomeStatus.STOPPED, ErrorCode.OUT_OF_MEMORY),
        (OutcomeStatus.CONVERTED, None),
    ]
