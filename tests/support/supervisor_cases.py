"""Limits, a planned item and a failure helper for the worker supervisor's tests."""

from pathlib import Path

import pytest

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.limits import MIB, Limits
from clearmd.backend.schemas.models import Detection, DetectionMethod, PlannedConversion
from clearmd.backend.services.worker.supervisor import WorkerRunner
from clearmd.backend.use_cases.cancel import CancelToken

TIGHT = Limits(time_per_file=1.0, worker_memory=200 * MIB)


def _item(
    name: str, format_id: FormatId = FormatId.TXT, folder: Path = Path("/fake")
) -> PlannedConversion:
    return PlannedConversion(
        source=folder / name,
        output_root=folder / "ClearMD_Output",
        target=folder / "ClearMD_Output" / "OutputMD" / f"{Path(name).stem}.md",
        detection=Detection(format_id, DetectionMethod.EXTENSION),
        exists=False,
        cost=1.0,
    )


def _fails_with(runner: WorkerRunner, name: str, code: ErrorCode) -> ConversionError:
    with pytest.raises(ConversionError) as raised:
        runner.convert(_item(name), CancelToken())
    assert raised.value.code is code
    return raised.value
