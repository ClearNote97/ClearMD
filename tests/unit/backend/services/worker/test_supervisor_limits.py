"""The worker supervisor (ADR-0015): memory caps and results."""

import sys
import time
from pathlib import Path

import psutil
import pytest
from support.supervisor_cases import TIGHT, _fails_with, _item
from support.worker_factories import FAKE

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind
from clearmd.backend.services.worker.supervisor import VIRTUAL_HEADROOM, WorkerRunner
from clearmd.backend.use_cases.cancel import CancelToken


@pytest.mark.skipif(sys.platform == "win32", reason="RLIMIT_AS is POSIX")
def test_the_worker_has_a_hard_memory_cap(runner: WorkerRunner) -> None:
    cap = int(runner.convert(_item("rlimit.txt"), CancelToken()).markdown)
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
    before = runner.convert(_item("pid.txt"), CancelToken()).markdown
    _fails_with(runner, "memoryerror.txt", ErrorCode.OUT_OF_MEMORY)
    assert runner.convert(_item("pid.txt"), CancelToken()).markdown != before


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


def test_notes_travel_back_from_the_worker(runner: WorkerRunner) -> None:
    result = runner.convert(_item("noted.txt"), CancelToken())
    assert result.notes == (
        ConversionNote(NoteKind.UNKNOWN_COMMANDS, (NoteItem("\\foo"), NoteItem("\\bar"))),
    )
