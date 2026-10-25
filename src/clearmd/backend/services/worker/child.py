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
from clearmd.backend.services.worker.protocol import Converted, ConvertRequest, Failed, Response


class _Registry(Protocol):
    def for_format(self, format_id: FormatId) -> DocumentConverter: ...


def load_factory(path: str) -> _Registry:
    """Build the registry named by ``"package.module:function"``."""
    module_name, _, function_name = path.partition(":")
    factory = getattr(importlib.import_module(module_name), function_name)
    registry: _Registry = factory()
    return registry


def handle(registry: _Registry, request: ConvertRequest) -> Response:
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
    while True:
        try:
            request = connection.recv()
        except EOFError:
            return
        if request is None:
            return
        connection.send(handle(registry, request))
