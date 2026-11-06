"""The worker process: builds its converters once and serves one request at a time."""

import importlib
import inspect
import signal
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any, Protocol

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId, Strategy
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind
from clearmd.backend.services.conversion.images import ImageSink
from clearmd.backend.services.conversion.registry import DocumentConverter
from clearmd.backend.services.worker.power import keep_full_speed
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
    def for_format(
        self, format_id: FormatId, strategy: Strategy = Strategy.FULL
    ) -> DocumentConverter: ...

    def detect_content(self, path: Path) -> Detection | None: ...


def load_factory(path: str) -> _Registry:
    """Build the registry named by ``"package.module:function"``."""
    module_name, _, function_name = path.partition(":")
    factory = getattr(importlib.import_module(module_name), function_name)
    registry: _Registry = factory()
    return registry


def apply_memory_cap(limit: int) -> None:
    """A hard cap from the OS, so one huge allocation fails at once (POSIX; Windows: feature 006).

    The supervisor samples the memory every 0.1 s, but a single decompression can ask for
    gigabytes in one call (security review of feature 001). RLIMIT_AS counts virtual memory, so
    the cap includes room for what the libraries reserve but do not use.
    """
    try:
        import resource
    except ImportError:
        return
    _, hard = resource.getrlimit(resource.RLIMIT_AS)
    if hard != resource.RLIM_INFINITY:
        limit = min(limit, hard)  # a lower limit inherited from the system wins
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))


def handle(
    registry: _Registry, request: ConvertRequest | DetectRequest, max_result_chars: int
) -> Response:
    if isinstance(request, DetectRequest):
        try:
            detection = registry.detect_content(Path(request.source))
        except MemoryError:  # the worker is replaced: its memory is no longer to be trusted
            return Failed(ErrorCode.OUT_OF_MEMORY.value, "MemoryError: over the hard memory cap")
        except Exception as error:
            return Failed(ErrorCode.CONVERSION_FAILED.value, f"{type(error).__name__}: {error}")
        return Detected(detection.format.value if detection is not None else None)
    format_id = FormatId(request.format)
    detection = Detection(format_id, DetectionMethod(request.method))
    try:
        converter = registry.for_format(format_id, Strategy(request.strategy))
        # The images, only when asked and only to a converter that keeps them (012): TeX and
        # Excel take no sink, and handing them one failed every such file (found in R01).
        keeps = "images" in inspect.signature(converter.convert).parameters
        sink = ImageSink.for_folder(request.images) if request.images and keeps else None
        options: dict[str, Any] = {"images": sink} if sink is not None else {}
        result = converter.convert(Path(request.source), detection, Path(request.target), **options)
    except ConversionError as error:
        return Failed(error.code.value, error.detail)
    except MemoryError:
        return Failed(ErrorCode.OUT_OF_MEMORY.value, "MemoryError: over the hard memory cap")
    except Exception as error:
        return Failed(ErrorCode.CONVERSION_FAILED.value, f"{type(error).__name__}: {error}")
    if len(result.markdown) > max_result_chars:  # never ship gigabytes back to the interface
        return Failed(
            ErrorCode.CONVERSION_FAILED.value,
            f"result too large: {len(result.markdown)} characters, limit {max_result_chars}",
        )
    notes = result.notes
    if sink is not None and sink.left_out:  # pictures a viewer cannot show, or past the limits
        notes = (*notes, ConversionNote(NoteKind.IMAGES_LEFT_OUT, (NoteItem(str(sink.left_out)),)))
    images = tuple(sink.images) if sink is not None else result.images
    return Converted(result.markdown, notes, images)


def worker_main(
    connection: Connection,
    factory_path: str,
    memory_cap: int | None = None,
    max_result_chars: int = 512 * 1024**2,
) -> None:
    # Ctrl+C reaches the whole process group; only the supervisor decides what to stop.
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    keep_full_speed()  # Windows: never throttled as background work (power.py, v1.0.1)
    if memory_cap is not None:
        apply_memory_cap(memory_cap)
    registry = load_factory(factory_path)
    connection.send(Ready())
    while True:
        try:
            request: Request = connection.recv()
        except EOFError:
            return
        if request is None:
            return
        connection.send(handle(registry, request, max_result_chars))
