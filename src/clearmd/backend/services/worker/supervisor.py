"""Runs conversions in a worker process and enforces the limits of ADR-0015."""

import multiprocessing
import time
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from pathlib import Path

import psutil

from clearmd.backend.schemas.errors import Cancelled, ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.models import Detection, DetectionMethod, PlannedConversion
from clearmd.backend.services.worker.child import worker_main
from clearmd.backend.services.worker.protocol import (
    Converted,
    ConvertRequest,
    Detected,
    DetectRequest,
    Failed,
    Ready,
    Request,
    Response,
)
from clearmd.backend.use_cases.cancel import CancelToken

REAL_REGISTRY = "clearmd.backend.services.conversion.registry:build_registry"
POLL_SECONDS = 0.1
JOIN_SECONDS = 5.0
# Loading Python, markitdown and the magika model; generous for packaged apps and antivirus scans.
STARTUP_SECONDS = 120.0
# Virtual memory the libraries reserve without using it (a loaded worker: ~1.4 GiB virtual for
# ~170 MiB resident, mostly onnxruntime threads); the OS hard cap is the limit plus this.
VIRTUAL_HEADROOM = 2 * 1024**3


class WorkerRunner:
    """A ``ConversionRunner`` and a content ``FormatDetector``: one persistent worker, replaced
    whenever it has to be stopped."""

    def __init__(self, factory_path: str = REAL_REGISTRY, limits: Limits | None = None) -> None:
        self._factory_path = factory_path
        self._limits = limits or Limits()
        # spawn on every OS: the same behavior Windows will have.
        self._context = multiprocessing.get_context("spawn")
        self._process: BaseProcess | None = None
        self._connection: Connection | None = None

    @property
    def pid(self) -> int | None:
        return self._process.pid if self._process is not None else None

    def convert(self, item: PlannedConversion, cancel: CancelToken) -> str:
        if cancel.is_set():
            raise Cancelled
        request = ConvertRequest(
            str(item.source), item.detection.format.value, item.detection.method.value
        )
        response = self._request(request, cancel)
        if not isinstance(response, Converted):
            raise ConversionError(ErrorCode.CONVERSION_FAILED, f"unexpected reply {response!r}")
        return response.markdown

    def warm_up(self, cancel: CancelToken) -> None:
        """Start the worker now, so no file's time includes the start-up (AC-41)."""
        self._ensure_worker(cancel)

    def detect(self, path: Path) -> Detection | None:
        """The format of ``path`` by its content; any failure means "unsupported"."""
        try:
            response = self._request(DetectRequest(str(path)), CancelToken())
        except ConversionError:
            return None
        if not isinstance(response, Detected) or response.format is None:
            return None
        return Detection(FormatId(response.format), DetectionMethod.CONTENT)

    def _request(self, request: Request, cancel: CancelToken) -> Response:
        connection, process = self._ensure_worker(cancel)
        try:
            connection.send(request)
        except OSError:  # it died while idle (e.g. the system's OOM killer)
            raise self._crashed(process) from None
        return self._wait(connection, process, cancel)

    def close(self) -> None:
        if self._process is None or self._connection is None:
            return
        try:
            self._connection.send(None)
        except OSError:
            pass
        self._process.join(JOIN_SECONDS)
        self._stop()

    def _ensure_worker(self, cancel: CancelToken) -> tuple[Connection, BaseProcess]:
        if self._process is not None and self._connection is not None and self._process.is_alive():
            return self._connection, self._process
        self._stop()
        parent_end, child_end = self._context.Pipe()
        memory_cap = self._limits.worker_memory + VIRTUAL_HEADROOM
        process = self._context.Process(
            target=worker_main, args=(child_end, self._factory_path, memory_cap), daemon=True
        )
        process.start()
        child_end.close()
        self._process, self._connection = process, parent_end
        self._wait_until_ready(parent_end, process, cancel)
        return parent_end, process

    def _wait_until_ready(
        self, connection: Connection, process: BaseProcess, cancel: CancelToken
    ) -> None:
        """Start-up is not a file's time: wait for ``Ready`` with its own limit."""
        started = time.monotonic()
        while not connection.poll(POLL_SECONDS):
            if cancel.is_set():
                self._stop()
                raise Cancelled
            if not process.is_alive():
                raise self._crashed(process)
            if time.monotonic() - started > STARTUP_SECONDS:
                self._stop()
                raise ConversionError(
                    ErrorCode.WORKER_CRASHED, f"worker not ready after {STARTUP_SECONDS:g} s"
                )
        try:
            message = connection.recv()
        except EOFError:
            raise self._crashed(process) from None
        if not isinstance(message, Ready):
            self._stop()
            raise ConversionError(ErrorCode.WORKER_CRASHED, f"unexpected start-up {message!r}")

    def _wait(self, connection: Connection, process: BaseProcess, cancel: CancelToken) -> Response:
        started = time.monotonic()
        while True:
            if connection.poll(POLL_SECONDS):
                try:
                    response: Response = connection.recv()
                except EOFError:
                    raise self._crashed(process) from None
                if isinstance(response, Failed):
                    raise ConversionError(ErrorCode(response.code), response.detail)
                return response
            if cancel.is_set():
                self._stop()
                raise Cancelled
            elapsed = time.monotonic() - started
            if elapsed > self._limits.time_per_file:
                self._stop()
                raise ConversionError(
                    ErrorCode.TIMED_OUT, f"stopped after {self._limits.time_per_file:g} s"
                )
            rss = _memory_of(process)
            if rss is not None and rss > self._limits.worker_memory:
                self._stop()
                limit_mib = self._limits.worker_memory // 1024**2
                raise ConversionError(
                    ErrorCode.OUT_OF_MEMORY,
                    f"worker used {rss // 1024**2} MiB, limit {limit_mib} MiB",
                )
            if not process.is_alive():
                raise self._crashed(process)

    def _crashed(self, process: BaseProcess) -> ConversionError:
        process.join(JOIN_SECONDS)
        exit_code = process.exitcode
        self._stop()
        return ConversionError(ErrorCode.WORKER_CRASHED, f"worker exited with code {exit_code}")

    def _stop(self) -> None:
        if self._process is not None:
            _kill_children(self._process)
            if self._process.is_alive():
                self._process.kill()
            self._process.join(JOIN_SECONDS)
            self._process.close()
        if self._connection is not None:
            self._connection.close()
        self._process, self._connection = None, None


def _kill_children(process: BaseProcess) -> None:
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


def _memory_of(process: BaseProcess) -> int | None:
    if process.pid is None:
        return None
    try:
        rss: int = psutil.Process(process.pid).memory_info().rss
    except psutil.Error:
        return None
    return rss
