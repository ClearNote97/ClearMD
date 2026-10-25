from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from clearmd.backend.schemas.errors import Cancelled, ConversionError, ErrorCode
from clearmd.backend.schemas.events import BatchEvent, ConversionFinished, ConversionStarted
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import (
    BatchPlan,
    BatchReport,
    Detection,
    DetectionMethod,
    OutcomeStatus,
    PlannedConversion,
)
from clearmd.backend.use_cases.cancel import CancelToken
from clearmd.backend.use_cases.execution import atomic_write, execute_plan

NOW = datetime(2026, 10, 25, 15, 30, tzinfo=UTC)


class FixedClock:
    def now(self) -> datetime:
        return NOW


class FakeRunner:
    """Converts by file stem: "corrupt" fails, "cancel" sets the token mid-file."""

    def __init__(self, cancel: CancelToken | None = None) -> None:
        self.cancel = cancel
        self.seen: list[str] = []

    def convert(self, item: PlannedConversion, cancel: CancelToken) -> str:
        self.seen.append(item.source.name)
        if cancel.is_set():
            raise Cancelled
        if item.source.stem == "corrupt":
            raise ConversionError(ErrorCode.CORRUPT_FILE, "BadZipFile: File is not a zip file")
        if item.source.stem == "cancel":
            cancel.cancel()
            raise Cancelled
        return f"# {item.source.stem}\r\nline two\r\n"

    def warm_up(self, cancel: CancelToken) -> None:
        pass

    def close(self) -> None:
        pass


def _item(folder: Path, name: str, *, exists: bool = False) -> PlannedConversion:
    root = folder / "ClearMD_Output"
    return PlannedConversion(
        source=folder / name,
        output_root=root,
        target=root / "OutputMD" / f"{Path(name).stem}.md",
        detection=Detection(FormatId.PDF, DetectionMethod.EXTENSION),
        exists=exists,
        cost=1.0,
    )


def _run(
    plan: BatchPlan,
    runner: FakeRunner,
    *,
    overwrite: Callable[[PlannedConversion], bool] = lambda item: True,
) -> tuple[list[BatchEvent], BatchReport]:
    events: list[BatchEvent] = []
    report = execute_plan(
        plan,
        overwrite=overwrite,
        runner=runner,
        on_event=events.append,
        cancel=CancelToken(),
        clock=FixedClock(),
    )
    return events, report


def _plan(*items: PlannedConversion) -> BatchPlan:
    return BatchPlan(conversions=items, skipped=(), input_errors=())


def test_converted_files_are_written_utf8_with_lf(tmp_path: Path) -> None:
    item = _item(tmp_path, "report.pdf")
    events, report = _run(_plan(item), FakeRunner())
    assert item.target.read_bytes() == b"# report\nline two\n"
    assert [o.status for o in report.outcomes] == [OutcomeStatus.CONVERTED]
    assert [type(e) for e in events] == [ConversionStarted, ConversionFinished]


def test_a_failure_does_not_stop_the_batch(tmp_path: Path) -> None:
    items = (_item(tmp_path, "corrupt.pdf"), _item(tmp_path, "good.pdf"))
    _, report = _run(_plan(*items), FakeRunner())
    outcomes = report.outcomes
    assert [o.status for o in outcomes] == [OutcomeStatus.FAILED, OutcomeStatus.CONVERTED]
    assert outcomes[0].error is ErrorCode.CORRUPT_FILE
    assert outcomes[0].detail == "BadZipFile: File is not a zip file"
    assert not items[0].target.exists()
    assert items[1].target.exists()


def test_existing_outputs_are_kept_when_the_caller_says_so(tmp_path: Path) -> None:
    item = _item(tmp_path, "report.pdf", exists=True)
    item.target.parent.mkdir(parents=True)
    item.target.write_text("old", encoding="utf-8")
    runner = FakeRunner()
    _, report = _run(_plan(item), runner, overwrite=lambda item: False)
    assert item.target.read_text(encoding="utf-8") == "old"
    assert runner.seen == []
    assert [o.status for o in report.outcomes] == [OutcomeStatus.KEPT]


def test_cancelling_marks_the_current_and_the_rest_as_cancelled(tmp_path: Path) -> None:
    items = (
        _item(tmp_path, "first.pdf"),
        _item(tmp_path, "cancel.pdf"),
        _item(tmp_path, "last.pdf"),
    )
    runner = FakeRunner()
    _, report = _run(_plan(*items), runner)
    statuses = [o.status for o in report.outcomes]
    assert statuses == [OutcomeStatus.CONVERTED, OutcomeStatus.CANCELLED, OutcomeStatus.CANCELLED]
    assert report.cancelled
    assert runner.seen == ["first.pdf", "cancel.pdf"]
    assert not items[1].target.exists()


def test_report_carries_the_clock_and_the_plan(tmp_path: Path) -> None:
    _, report = _run(_plan(_item(tmp_path, "a.pdf")), FakeRunner())
    assert report.started_at == NOW
    assert report.finished_at == NOW


def test_a_permission_error_fails_that_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import clearmd.backend.use_cases.execution as execution

    def deny(target: Path, text: str) -> None:
        raise PermissionError(13, "Permission denied", str(target))

    monkeypatch.setattr(execution, "atomic_write", deny)
    _, report = _run(_plan(_item(tmp_path, "a.pdf")), FakeRunner())
    (outcome,) = report.outcomes
    assert outcome.error is ErrorCode.PERMISSION_DENIED


def test_atomic_write_leaves_no_temp_file(tmp_path: Path) -> None:
    target = tmp_path / "out" / "a.md"
    atomic_write(target, "hello\r\nworld")
    assert target.read_bytes() == b"hello\nworld"
    assert [p.name for p in target.parent.iterdir()] == ["a.md"]


def test_atomic_write_removes_the_temp_file_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import os

    def broken_replace(src: str, dst: str) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", broken_replace)
    target = tmp_path / "a.md"
    with pytest.raises(OSError, match="disk full"):
        atomic_write(target, "x")
    assert list(tmp_path.iterdir()) == []


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
    def convert(self, item: PlannedConversion, cancel: CancelToken) -> str:
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


def test_an_output_that_appeared_after_planning_is_not_overwritten_silently(tmp_path: Path) -> None:
    item = _item(tmp_path, "report.pdf")  # planned as not existing
    item.target.parent.mkdir(parents=True)
    item.target.write_text("written meanwhile", encoding="utf-8")
    asked: list[Path] = []

    def overwrite(planned: PlannedConversion) -> bool:
        asked.append(planned.target)
        return False

    _, report = _run(_plan(item), FakeRunner(), overwrite=overwrite)
    assert asked == [item.target]
    assert item.target.read_text(encoding="utf-8") == "written meanwhile"
    assert [o.status for o in report.outcomes] == [OutcomeStatus.KEPT]


def test_an_unwritable_output_root_fails_its_files_without_converting_them(tmp_path: Path) -> None:
    locked = tmp_path / "locked"
    locked.mkdir()
    free = tmp_path / "free"
    free.mkdir()
    items = (_item(locked, "a.pdf"), _item(locked, "b.pdf"), _item(free, "c.pdf"))
    runner = FakeRunner()
    locked.chmod(0o555)
    try:
        _, report = _run(_plan(*items), runner)
    finally:
        locked.chmod(0o755)
    outcomes = report.outcomes
    assert [o.error for o in outcomes[:2]] == [ErrorCode.PERMISSION_DENIED] * 2
    assert outcomes[2].status is OutcomeStatus.CONVERTED
    assert runner.seen == ["c.pdf"]  # nothing was converted for the locked root
