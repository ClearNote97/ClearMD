"""A fixed clock, a fake runner and plan builders for the execution tests."""

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from clearmd.backend.schemas.errors import Cancelled, ConversionError, ErrorCode
from clearmd.backend.schemas.events import BatchEvent
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import (
    BatchPlan,
    BatchReport,
    ConversionResult,
    Detection,
    DetectionMethod,
    PlannedConversion,
)
from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind
from clearmd.backend.use_cases.cancel import CancelToken
from clearmd.backend.use_cases.execution import execute_plan

NOW = datetime(2026, 10, 25, 15, 30, tzinfo=UTC)


class FixedClock:
    def now(self) -> datetime:
        return NOW


class FakeRunner:
    """Converts by file stem: "corrupt" fails, "cancel" sets the token mid-file."""

    def __init__(self, cancel: CancelToken | None = None) -> None:
        self.cancel = cancel
        self.seen: list[str] = []

    def convert(self, item: PlannedConversion, cancel: CancelToken) -> ConversionResult:
        self.seen.append(item.source.name)
        if cancel.is_set():
            raise Cancelled
        if item.source.stem == "corrupt":
            raise ConversionError(ErrorCode.CORRUPT_FILE, "BadZipFile: File is not a zip file")
        if item.source.stem == "cancel":
            cancel.cancel()
            raise Cancelled
        notes = (ConversionNote(NoteKind.UNKNOWN_COMMANDS, (NoteItem("\\x"),)),)
        return ConversionResult(
            f"# {item.source.stem}\r\nline two\r\n", notes if item.source.stem == "noted" else ()
        )

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
