"""The worker supervisor (ADR-0015): detection and start-up."""

import threading
import time
from pathlib import Path

import pytest
from builders.common import MARKERS
from support import DOCUMENTS_DIR
from support.supervisor_cases import TIGHT, _item
from support.worker_factories import REAL, SLOW_START, SLOW_START_SECONDS

from clearmd.backend.schemas.errors import Cancelled, ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.services.worker.supervisor import WorkerRunner
from clearmd.backend.use_cases.cancel import CancelToken


def test_real_markitdown_runs_in_the_worker() -> None:
    worker = WorkerRunner(REAL, Limits(time_per_file=60))
    try:
        item = _item("sample.pdf", FormatId.PDF, DOCUMENTS_DIR)
        assert MARKERS["sample.pdf"] in worker.convert(item, CancelToken()).markdown
        with pytest.raises(ConversionError) as raised:
            worker.convert(_item("encrypted.pdf", FormatId.PDF, DOCUMENTS_DIR), CancelToken())
        assert raised.value.code is ErrorCode.PASSWORD_PROTECTED
    finally:
        worker.close()


def test_content_detection_runs_in_the_worker(runner: WorkerRunner) -> None:
    detection = runner.detect(Path("/fake/detect_docx"))
    assert detection == Detection(FormatId.DOCX, DetectionMethod.CONTENT)
    assert runner.detect(Path("/fake/unknown_thing")) is None


def test_a_crash_while_detecting_means_unsupported_and_a_new_worker(runner: WorkerRunner) -> None:
    assert runner.detect(Path("/fake/crash")) is None
    assert runner.convert(_item("notes.txt"), CancelToken()).markdown == "# converted notes.txt"


def test_the_real_detection_by_content_runs_in_the_worker() -> None:
    worker = WorkerRunner(REAL, Limits(time_per_file=60))
    try:
        detection = worker.detect(DOCUMENTS_DIR / "docx_without_extension")
        assert detection == Detection(FormatId.DOCX, DetectionMethod.CONTENT)
    finally:
        worker.close()


def test_the_time_limit_does_not_count_the_worker_start_up() -> None:
    worker = WorkerRunner(SLOW_START, Limits(time_per_file=SLOW_START_SECONDS / 2))
    try:
        assert worker.convert(_item("notes.txt"), CancelToken()).markdown == "# converted notes.txt"
    finally:
        worker.close()


def test_cancelling_while_the_worker_starts(runner: WorkerRunner) -> None:
    worker = WorkerRunner(SLOW_START, TIGHT)
    cancel = CancelToken()
    threading.Timer(0.2, cancel.cancel).start()
    started = time.monotonic()
    try:
        with pytest.raises(Cancelled):
            worker.convert(_item("notes.txt"), cancel)
        assert time.monotonic() - started < SLOW_START_SECONDS
    finally:
        worker.close()


def test_warm_up_starts_the_worker_before_the_first_file() -> None:
    worker = WorkerRunner(SLOW_START, TIGHT)
    try:
        worker.warm_up(CancelToken())
        assert worker.pid is not None
        started = time.monotonic()
        assert worker.convert(_item("notes.txt"), CancelToken()).markdown == "# converted notes.txt"
        assert time.monotonic() - started < SLOW_START_SECONDS / 2  # no start-up inside
    finally:
        worker.close()
