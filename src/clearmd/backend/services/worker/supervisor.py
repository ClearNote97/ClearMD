"""Runs conversions in a worker process and enforces the limits of ADR-0015."""

import multiprocessing
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from pathlib import Path

from clearmd.backend.schemas.errors import Cancelled, ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.models import (
    ConversionResult,
    Detection,
    DetectionMethod,
    PlannedConversion,
)
from clearmd.backend.services.worker.processes import (
    JOIN_SECONDS,
    kill_children,
    wait_for_response,
    wait_until_ready,
)
from clearmd.backend.services.worker.protocol import (
    Converted,
    ConvertRequest,
    Detected,
    DetectRequest,
    Request,
    Response,
)
from clearmd.backend.use_cases.cancel import CancelToken

REAL_REGISTRY = "clearmd.backend.services.conversion.registry:build_registry"
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

    def convert(self, item: PlannedConversion, cancel: CancelToken) -> ConversionResult:
        if cancel.is_set():
            raise Cancelled
        request = ConvertRequest(
            str(item.source),
            item.detection.format.value,
            item.detection.method.value,
            str(item.target),
            item.strategy.value,
            item.images,
        )
        response = self._request(request, cancel)
        if not isinstance(response, Converted):
            raise ConversionError(ErrorCode.CONVERSION_FAILED, f"unexpected reply {response!r}")
        return ConversionResult(response.markdown, response.notes, response.images)

    def job(self, request: Request, cancel: CancelToken) -> Response:
        """Send one job to the worker (the page jobs of Split, ``PageRunner``)."""
        if cancel.is_set():
            raise Cancelled
        return self._request(request, cancel)

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
        return wait_for_response(
            connection, process, cancel, self._limits, self._stop, self._crashed
        )

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
        # Imported here: the worker's converters (PDFium, openpyxl...) are never loaded by the
        # windows or the command line themselves (ADR-0015; audit 2026-11-09, B2-04).
        from clearmd.backend.services.worker.child import worker_main  # noqa: PLC0415

        process = self._context.Process(
            target=worker_main,
            args=(child_end, self._factory_path, memory_cap, self._limits.max_result_chars),
            daemon=True,
        )
        process.start()
        child_end.close()
        self._process, self._connection = process, parent_end
        wait_until_ready(parent_end, process, cancel, self._stop, self._crashed)
        return parent_end, process

    def _crashed(self, process: BaseProcess) -> ConversionError:
        process.join(JOIN_SECONDS)
        exit_code = process.exitcode
        self._stop()
        return ConversionError(ErrorCode.WORKER_CRASHED, f"worker exited with code {exit_code}")

    def _stop(self) -> None:
        if self._process is not None:
            kill_children(self._process)
            if self._process.is_alive():
                self._process.kill()
            self._process.join(JOIN_SECONDS)
            self._process.close()
        if self._connection is not None:
            self._connection.close()
        self._process, self._connection = None, None
