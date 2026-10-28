"""Fakes for the presenter and the GUIs: a backend that plans and converts without converting."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from clearmd.backend.schemas.errors import ErrorCode
from clearmd.backend.schemas.events import BatchEvent, ConversionFinished, ConversionStarted
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import (
    BatchPlan,
    BatchReport,
    ConversionOutcome,
    Detection,
    DetectionMethod,
    OutcomeStatus,
    PlannedConversion,
)
from clearmd.backend.schemas.settings import Settings, SettingsWarning

NOW = datetime(2026, 10, 27, 12, 0)


def planned(name: str, *, exists: bool = False, cost: float = 1.0) -> PlannedConversion:
    source = Path("/docs") / name
    return PlannedConversion(
        source=source,
        output_root=Path("/docs/ClearMD_Output"),
        target=Path("/docs/ClearMD_Output/OutputMD") / f"{source.stem}.md",
        detection=Detection(FormatId.PDF, DetectionMethod.EXTENSION),
        exists=exists,
        cost=cost,
    )


@dataclass
class FakeBackend:
    settings: Settings = field(default_factory=Settings)
    warnings: tuple[SettingsWarning, ...] = ()
    plan: BatchPlan = field(default_factory=lambda: BatchPlan((planned("a.pdf"),), (), ()))
    statuses: dict[str, OutcomeStatus] = field(default_factory=dict)
    plan_calls: list[dict[str, Any]] = field(default_factory=list)
    run_calls: list[dict[str, Any]] = field(default_factory=list)
    saved: list[Settings] = field(default_factory=list)
    opened: list[Path] = field(default_factory=list)
    save_error: OSError | None = None
    plan_error: Exception | None = None
    before_finish: Callable[[], None] | None = None

    def load_settings(self) -> tuple[Settings, tuple[SettingsWarning, ...]]:
        return self.settings, self.warnings

    def save_settings(self, settings: Settings) -> None:
        if self.save_error is not None:
            raise self.save_error
        self.saved.append(settings)
        self.settings = settings

    def open_folder(self, path: Path) -> None:
        self.opened.append(path)

    def plan_batch(self, inputs: Sequence[Path], **kwargs: Any) -> BatchPlan:
        self.plan_calls.append({"inputs": list(inputs), **kwargs})
        if self.plan_error is not None:
            raise self.plan_error
        return self.plan

    def run_batch(self, plan: BatchPlan, **kwargs: Any) -> BatchReport:
        self.run_calls.append(kwargs)
        on_event: Callable[[BatchEvent], None] = kwargs["on_event"]
        outcomes = []
        total = len(plan.conversions)
        for index, item in enumerate(plan.conversions, start=1):
            on_event(ConversionStarted(index, total, item, seconds_left=120.0))
            if self.before_finish is not None:
                self.before_finish()
            if kwargs["cancel"].is_set():
                outcome = ConversionOutcome(item, OutcomeStatus.CANCELLED)
            else:
                status = self.statuses.get(item.source.name, OutcomeStatus.CONVERTED)
                if (
                    status is OutcomeStatus.CONVERTED
                    and item.exists
                    and not kwargs["overwrite"](item)
                ):
                    status = OutcomeStatus.KEPT
                error = ErrorCode.PASSWORD_PROTECTED if status is OutcomeStatus.FAILED else None
                if status is OutcomeStatus.STOPPED:
                    error = ErrorCode.TIMED_OUT
                outcome = ConversionOutcome(
                    item, status, error, limit=600 if error is ErrorCode.TIMED_OUT else None
                )
            outcomes.append(outcome)
            on_event(ConversionFinished(index, total, outcome))
        return BatchReport(
            NOW, NOW, tuple(outcomes), plan.skipped, plan.input_errors, kwargs["cancel"].is_set()
        )
