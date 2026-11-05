"""Watching the worker process: its children, its memory, and the two waiting loops.

``wait_until_ready`` and ``wait_for_response`` poll the pipe every 0.1 s and enforce the limits
of ADR-0015 (cancellation, time, memory, unexpected death). They do not own the worker: the
supervisor passes in what stops it (``stop``) and what builds the crash error (``crashed``).
"""

import time
from collections.abc import Callable
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess

import psutil

from clearmd.backend.schemas.errors import Cancelled, ConversionError, ErrorCode
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.services.worker.protocol import Failed, Ready, Response
from clearmd.backend.use_cases.cancel import CancelToken

POLL_SECONDS = 0.1
JOIN_SECONDS = 5.0
# Loading Python and the converters' libraries; generous for packaged apps and antivirus scans.
STARTUP_SECONDS = 120.0


def kill_children(process: BaseProcess) -> None:
    """Anything a converter started (e.g. a helper program) dies with the worker."""
    if process.pid is None:
        return
    try:
        children = psutil.Process(process.pid).children(recursive=True)
    except psutil.Error:
        return
    for child in children:
        try:
            child.kill()
        except psutil.Error:
            pass


def memory_of(process: BaseProcess) -> int | None:
    """The resident memory of ``process``, or ``None`` when it cannot be read."""
    if process.pid is None:
        return None
    try:
        rss: int = psutil.Process(process.pid).memory_info().rss
    except psutil.Error:
        return None
    return rss


def wait_until_ready(
    connection: Connection,
    process: BaseProcess,
    cancel: CancelToken,
    stop: Callable[[], None],
    crashed: Callable[[BaseProcess], ConversionError],
) -> None:
    """Start-up is not a file's time: wait for ``Ready`` with its own limit."""
    started = time.monotonic()
    while not connection.poll(POLL_SECONDS):
        if cancel.is_set():
            stop()
            raise Cancelled
        if not process.is_alive():
            raise crashed(process)
        if time.monotonic() - started > STARTUP_SECONDS:
            stop()
            raise ConversionError(
                ErrorCode.WORKER_CRASHED, f"worker not ready after {STARTUP_SECONDS:g} s"
            )
    try:
        message = connection.recv()
    except EOFError:
        raise crashed(process) from None
    if not isinstance(message, Ready):
        stop()
        raise ConversionError(ErrorCode.WORKER_CRASHED, f"unexpected start-up {message!r}")


def wait_for_response(
    connection: Connection,
    process: BaseProcess,
    cancel: CancelToken,
    limits: Limits,
    stop: Callable[[], None],
    crashed: Callable[[BaseProcess], ConversionError],
) -> Response:
    """The worker's answer to the request just sent, under the time and memory limits."""
    started = time.monotonic()
    while True:
        if connection.poll(POLL_SECONDS):
            try:
                response: Response = connection.recv()
            except EOFError:
                raise crashed(process) from None
            if isinstance(response, Failed):
                limit = None
                if response.code == ErrorCode.OUT_OF_MEMORY.value:
                    stop()  # after a MemoryError the worker's heap is not trusted
                    limit = limits.worker_memory
                raise ConversionError(ErrorCode(response.code), response.detail, limit=limit)
            return response
        if cancel.is_set():
            stop()
            raise Cancelled
        elapsed = time.monotonic() - started
        if elapsed > limits.time_per_file:
            stop()
            raise ConversionError(
                ErrorCode.TIMED_OUT,
                f"stopped after {limits.time_per_file:g} s",
                limit=limits.time_per_file,
            )
        rss = memory_of(process)
        if rss is not None and rss > limits.worker_memory:
            stop()
            limit_mib = limits.worker_memory // 1024**2
            raise ConversionError(
                ErrorCode.OUT_OF_MEMORY,
                f"worker used {rss // 1024**2} MiB, limit {limit_mib} MiB",
                limit=limits.worker_memory,
            )
        if not process.is_alive():
            raise crashed(process)
