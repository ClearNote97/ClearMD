"""The worker's page jobs (Split, feature 023): count a PDF's pages, copy some into a new PDF."""

from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.services.split.pdf_pages import count_pages, cut_pages
from clearmd.backend.services.worker.protocol import (
    Counted,
    CountPagesRequest,
    CutDone,
    CutRequest,
    Failed,
    Response,
)


def handle_pages(request: CountPagesRequest | CutRequest, max_result_bytes: int) -> Response:
    try:
        if isinstance(request, CountPagesRequest):
            return Counted(count_pages(Path(request.source)))
        data = cut_pages(Path(request.source), request.first, request.last)
    except ConversionError as error:
        return Failed(error.code.value, error.detail)
    except MemoryError:
        return Failed(ErrorCode.OUT_OF_MEMORY.value, "MemoryError: over the hard memory cap")
    except Exception as error:
        return Failed(ErrorCode.CONVERSION_FAILED.value, f"{type(error).__name__}: {error}")
    if len(data) > max_result_bytes:  # never ship gigabytes back to the interface
        return Failed(
            ErrorCode.CONVERSION_FAILED.value,
            f"part too large: {len(data)} bytes, limit {max_result_bytes}",
        )
    return CutDone(data)
