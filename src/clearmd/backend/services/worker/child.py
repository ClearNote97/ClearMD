"""The worker process: builds its converters once and serves one request at a time."""

import importlib
import signal
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Protocol

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.services.conversion.registry import DocumentConverter
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


class _Registry(Protocol):
    def for_format(self, format_id: FormatId) -> DocumentConverter: ...

    def detect_content(self, path: Path) -> Detection | None: ...


def load_factory(path: str) -> _Registry:
    """Build the registry named by ``"package.module:function"``."""
    module_name, _, function_name = path.partition(":")
    factory = getattr(importlib.import_module(module_name), function_name)
    registry: _Registry = factory()
    return registry


def handle(registry: _Registry, request: ConvertRequest | DetectRequest) -> Response:
    if isinstance(request, DetectRequest):
        try:
            detection = registry.detect_content(Path(request.source))
        except Exception as error:
            return Failed(ErrorCode.CONVERSION_FAILED.value, f"{type(error).__name__}: {error}")
        return Detected(detection.format.value if detection is not None else None)
    format_id = FormatId(request.format)
    detection = Detection(format_id, DetectionMethod(request.method))
    try:
        markdown = registry.for_format(format_id).convert(Path(request.source), detection)
    except ConversionError as error:
        return Failed(error.code.value, error.detail)
    except Exception as error:
        return Failed(ErrorCode.CONVERSION_FAILED.value, f"{type(error).__name__}: {error}")
    return Converted(markdown)


def worker_main(connection: Connection, factory_path: str) -> None:
    # Ctrl+C reaches the whole process group; only the supervisor decides what to stop.
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    registry = load_factory(factory_path)
    connection.send(Ready())
    while True:
        try:
            request: Request = connection.recv()
        except EOFError:
            return
        if request is None:
            return
        connection.send(handle(registry, request))
