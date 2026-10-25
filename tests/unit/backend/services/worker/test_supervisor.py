"""The supervisor enforces time, memory and cancellation, and replaces the worker (ADR-0015)."""

import sys
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import psutil
import pytest
from build_fixtures import MARKERS
from support import DOCUMENTS_DIR
from support.worker_factories import FAKE, REAL, SLOW_START, SLOW_START_SECONDS

from clearmd.backend.schemas.errors import Cancelled, ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.limits import MIB, Limits
from clearmd.backend.schemas.models import Detection, DetectionMethod, PlannedConversion
from clearmd.backend.services.worker.supervisor import VIRTUAL_HEADROOM, WorkerRunner
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


@pytest.fixture
def runner() -> Iterator[WorkerRunner]:
    worker = WorkerRunner(FAKE, TIGHT)
    yield worker
    worker.close()


def _fails_with(runner: WorkerRunner, name: str, code: ErrorCode) -> ConversionError:
    with pytest.raises(ConversionError) as raised:
        runner.convert(_item(name), CancelToken())
    assert raised.value.code is code
    return raised.value


def test_converts_through_the_worker(runner: WorkerRunner) -> None:
    assert runner.convert(_item("notes.txt"), CancelToken()) == "# converted notes.txt"


def test_the_worker_is_reused_between_files(runner: WorkerRunner) -> None:
    first = runner.convert(_item("pid.txt"), CancelToken())
    second = runner.convert(_item("pid.txt"), CancelToken())
    assert first == second == str(runner.pid)


def test_a_known_failure_keeps_its_code_and_the_worker(runner: WorkerRunner) -> None:
    pid = runner.convert(_item("pid.txt"), CancelToken())
    error = _fails_with(runner, "corrupt.txt", ErrorCode.CORRUPT_FILE)
    assert error.detail == "BadZipFile: File is not a zip file"
    assert runner.convert(_item("pid.txt"), CancelToken()) == pid


def test_an_unexpected_exception_is_a_conversion_failure(runner: WorkerRunner) -> None:
    error = _fails_with(runner, "boom.txt", ErrorCode.CONVERSION_FAILED)
    assert error.detail == "RuntimeError: unexpected failure"


def test_a_slow_file_times_out_and_the_worker_is_replaced(runner: WorkerRunner) -> None:
    before = runner.convert(_item("pid.txt"), CancelToken())
    started = time.monotonic()
    _fails_with(runner, "slow.txt", ErrorCode.TIMED_OUT)
    assert time.monotonic() - started < TIGHT.time_per_file + 2
    after = runner.convert(_item("pid.txt"), CancelToken())
    assert after != before


def test_a_memory_hog_is_stopped(runner: WorkerRunner) -> None:
    _fails_with(runner, "hog.txt", ErrorCode.OUT_OF_MEMORY)
    assert runner.convert(_item("notes.txt"), CancelToken()) == "# converted notes.txt"


def test_a_crash_is_reported_and_the_batch_can_go_on(runner: WorkerRunner) -> None:
    error = _fails_with(runner, "crash.txt", ErrorCode.WORKER_CRASHED)
    assert "3" in error.detail
    assert runner.convert(_item("notes.txt"), CancelToken()) == "# converted notes.txt"


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


def test_real_markitdown_runs_in_the_worker() -> None:
    worker = WorkerRunner(REAL, Limits(time_per_file=60))
    try:
        markdown = worker.convert(_item("sample.pdf", FormatId.PDF, DOCUMENTS_DIR), CancelToken())
        assert MARKERS["sample.pdf"] in markdown
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
    assert runner.convert(_item("notes.txt"), CancelToken()) == "# converted notes.txt"


def test_real_magika_detects_in_the_worker() -> None:
    worker = WorkerRunner(REAL, Limits(time_per_file=60))
    try:
        detection = worker.detect(DOCUMENTS_DIR / "docx_without_extension")
        assert detection == Detection(FormatId.DOCX, DetectionMethod.CONTENT)
    finally:
        worker.close()


def test_the_time_limit_does_not_count_the_worker_start_up() -> None:
    worker = WorkerRunner(SLOW_START, Limits(time_per_file=SLOW_START_SECONDS / 2))
    try:
        assert worker.convert(_item("notes.txt"), CancelToken()) == "# converted notes.txt"
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
        assert worker.convert(_item("notes.txt"), CancelToken()) == "# converted notes.txt"
        assert time.monotonic() - started < SLOW_START_SECONDS / 2  # no start-up inside
    finally:
        worker.close()


@pytest.mark.skipif(sys.platform == "win32", reason="RLIMIT_AS is POSIX")
def test_the_worker_has_a_hard_memory_cap(runner: WorkerRunner) -> None:
    cap = int(runner.convert(_item("rlimit.txt"), CancelToken()))
    assert cap == TIGHT.worker_memory + VIRTUAL_HEADROOM


def test_a_memory_error_inside_the_worker_is_a_memory_stop(runner: WorkerRunner) -> None:
    _fails_with(runner, "memoryerror.txt", ErrorCode.OUT_OF_MEMORY)


def test_stopping_the_worker_also_stops_what_it_started(tmp_path: Path) -> None:
    worker = WorkerRunner(FAKE, TIGHT)
    try:
        with pytest.raises(ConversionError):
            worker.convert(_item("spawn.txt", folder=tmp_path), CancelToken())
    finally:
        worker.close()
    grandchild = int((tmp_path / "grandchild.pid").read_text(encoding="utf-8"))
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            if psutil.Process(grandchild).status() == psutil.STATUS_ZOMBIE:
                break
        except psutil.NoSuchProcess:
            break
        time.sleep(0.1)
    else:
        pytest.fail("the grandchild process is still running")


def test_a_worker_that_died_while_idle_is_reported_not_raised(runner: WorkerRunner) -> None:
    runner.warm_up(CancelToken())

    def broken_pipe(message: object) -> None:
        raise BrokenPipeError(32, "Broken pipe")

    runner._connection.send = broken_pipe  # type: ignore[method-assign, union-attr]
    _fails_with(runner, "notes.txt", ErrorCode.WORKER_CRASHED)


def test_a_worker_is_replaced_after_a_memory_error(runner: WorkerRunner) -> None:
    before = runner.convert(_item("pid.txt"), CancelToken())
    _fails_with(runner, "memoryerror.txt", ErrorCode.OUT_OF_MEMORY)
    assert runner.convert(_item("pid.txt"), CancelToken()) != before


def test_the_memory_cap_respects_a_lower_inherited_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    resource = pytest.importorskip("resource")
    from clearmd.backend.services.worker.child import apply_memory_cap

    calls: list[tuple[int, int]] = []
    monkeypatch.setattr(resource, "getrlimit", lambda kind: (1024**3, 1024**3))
    monkeypatch.setattr(resource, "setrlimit", lambda kind, limits: calls.append(limits))
    apply_memory_cap(8 * 1024**3)
    assert calls == [(1024**3, 1024**3)]


def test_a_huge_result_is_refused_in_the_worker() -> None:
    worker = WorkerRunner(FAKE, Limits(time_per_file=10, max_result_chars=1000))
    try:
        error = _fails_with(worker, "huge_result.txt", ErrorCode.CONVERSION_FAILED)
        assert "too large" in error.detail
    finally:
        worker.close()
