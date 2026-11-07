"""The worker's page jobs (Split, feature 023): count a PDF's pages, copy some into a new PDF."""

from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.split import Cut
from clearmd.backend.services.split.markdown_cut import cut_markdown
from clearmd.backend.services.split.pdf_pages import count_pages, cut_pages
from clearmd.backend.services.split.words import page_words
from clearmd.backend.services.worker.protocol import (
    Counted,
    CountPagesRequest,
    CutDone,
    Failed,
    MarkdownCutRequest,
    MarkdownParts,
    PageJob,
    Response,
    Words,
    WordsRequest,
)


def _markdown(request: MarkdownCutRequest, max_result_bytes: int) -> Response:
    source = Path(request.source)
    if source.stat().st_size > max_result_bytes:
        return Failed(ErrorCode.CONVERSION_FAILED.value, "file too large to split")
    # Imported here: its module brings pylatexenc, which only TeX needs at start (feature 002).
    from clearmd.backend.services.conversion.tex.source import decode_source

    text = decode_source(source.read_bytes()).text
    parts, over = cut_markdown(text, Cut(request.cut), request.size)
    return MarkdownParts(parts, over)


def handle_pages(request: PageJob, max_result_bytes: int) -> Response:
    try:
        if isinstance(request, CountPagesRequest):
            return Counted(count_pages(Path(request.source)))
        if isinstance(request, WordsRequest):
            return Words(page_words(Path(request.source)))
        if isinstance(request, MarkdownCutRequest):
            return _markdown(request, max_result_bytes)
        data = cut_pages(Path(request.source), request.first, request.last)
    except ConversionError as error:
        return Failed(error.code.value, error.detail)
    except OSError as error:
        return Failed(ErrorCode.SOURCE_UNREADABLE.value, f"{type(error).__name__}: {error}")
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
