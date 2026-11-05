"""The worker supervisor (ADR-0015): converting, failing, timing out and cancelling."""

import threading
import time

import pytest
from support.supervisor_cases import TIGHT, _fails_with, _item
from support.worker_factories import FAKE

from clearmd.backend.schemas.errors import Cancelled, ErrorCode
from clearmd.backend.services.worker.supervisor import WorkerRunner
from clearmd.backend.use_cases.cancel import CancelToken


def test_converts_through_the_worker(runner: WorkerRunner) -> None:
    assert runner.convert(_item("notes.txt"), CancelToken()).markdown == "# converted notes.txt"


def test_the_worker_is_reused_between_files(runner: WorkerRunner) -> None:
    first = runner.convert(_item("pid.txt"), CancelToken()).markdown
    second = runner.convert(_item("pid.txt"), CancelToken()).markdown
    assert first == second == str(runner.pid)


def test_a_known_failure_keeps_its_code_and_the_worker(runner: WorkerRunner) -> None:
    pid = runner.convert(_item("pid.txt"), CancelToken()).markdown
    error = _fails_with(runner, "corrupt.txt", ErrorCode.CORRUPT_FILE)
    assert error.detail == "BadZipFile: File is not a zip file"
    assert runner.convert(_item("pid.txt"), CancelToken()).markdown == pid


def test_an_unexpected_exception_is_a_conversion_failure(runner: WorkerRunner) -> None:
    error = _fails_with(runner, "boom.txt", ErrorCode.CONVERSION_FAILED)
    assert error.detail == "RuntimeError: unexpected failure"


def test_a_slow_file_times_out_and_the_worker_is_replaced(runner: WorkerRunner) -> None:
    before = runner.convert(_item("pid.txt"), CancelToken()).markdown
    started = time.monotonic()
    _fails_with(runner, "slow.txt", ErrorCode.TIMED_OUT)
    assert time.monotonic() - started < TIGHT.time_per_file + 2
    after = runner.convert(_item("pid.txt"), CancelToken()).markdown
    assert after != before


def test_a_memory_hog_is_stopped(runner: WorkerRunner) -> None:
    _fails_with(runner, "hog.txt", ErrorCode.OUT_OF_MEMORY)
    assert runner.convert(_item("notes.txt"), CancelToken()).markdown == "# converted notes.txt"


def test_a_crash_is_reported_and_the_batch_can_go_on(runner: WorkerRunner) -> None:
    error = _fails_with(runner, "crash.txt", ErrorCode.WORKER_CRASHED)
    assert "3" in error.detail
    assert runner.convert(_item("notes.txt"), CancelToken()).markdown == "# converted notes.txt"


def test_cancelling_stops_the_current_file_at_once(runner: WorkerRunner) -> None:
    runner.convert(_item("notes.txt"), CancelToken())  # worker already up
    cancel = CancelToken()
    threading.Timer(0.2, cancel.cancel).start()
    started = time.monotonic()
    with pytest.raises(Cancelled):
        runner.convert(_item("slow.txt"), cancel)
    assert time.monotonic() - started < 1.0
    assert runner.pid is None  # the worker was stopped


def test_an_already_cancelled_token_converts_nothing(runner: WorkerRunner) -> None:
    cancel = CancelToken()
    cancel.cancel()
    with pytest.raises(Cancelled):
        runner.convert(_item("notes.txt"), cancel)


def test_the_network_guard_holds_inside_the_worker(runner: WorkerRunner) -> None:
    error = _fails_with(runner, "network.txt", ErrorCode.CONVERSION_FAILED)
    assert "NetworkBlockedError" in error.detail


def test_close_stops_the_worker() -> None:
    worker = WorkerRunner(FAKE, TIGHT)
    worker.convert(_item("notes.txt"), CancelToken())
    worker.close()
    assert worker.pid is None
    worker.close()  # idempotent
