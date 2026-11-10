"""The worker's page jobs (Split, feature 023): count a PDF's pages, copy some into a new PDF."""

from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.split import Cut
from clearmd.backend.services.conversion.markdown_out.safe_output import safe_output
from clearmd.backend.services.split.markdown_cut import cut_markdown
from clearmd.backend.services.split.pdf_pages import count_pages, cut_pages, merge_pdfs
from clearmd.backend.services.split.text_cut import cut_text
from clearmd.backend.services.split.words import page_words
from clearmd.backend.services.split.xlsx_cut import cut_xlsx
from clearmd.backend.services.worker.protocol import (
    Counted,
    CountPagesRequest,
    CutDone,
    Failed,
    FileParts,
    MarkdownCutRequest,
    MarkdownParts,
    MergePdfRequest,
    PageJob,
    ReadTextRequest,
    Response,
    TextCutRequest,
    TextRead,
    Words,
    WordsRequest,
    XlsxCutRequest,
)


def _text(path: str, max_result_bytes: int) -> str:
    """A text file's text, its encoding guessed when it is not UTF-8."""
    source = Path(path)
    if source.stat().st_size > max_result_bytes:
        raise ConversionError(ErrorCode.CONVERSION_FAILED, "file too large")
    # Imported here: its module brings pylatexenc, which only TeX needs at start (feature 002).
    from clearmd.backend.services.conversion.tex.source import decode_source

    return decode_source(source.read_bytes()).text


def _markdown(request: MarkdownCutRequest, max_result_bytes: int) -> Response:
    text = _text(request.source, max_result_bytes)
    parts, over = cut_markdown(text, Cut(request.cut), request.size)
    # A Markdown file's parts are results too: the same door as every result (audit v4, B2-02).
    return MarkdownParts(tuple(safe_output(part)[0] for part in parts), over)


def handle_pages(request: PageJob, max_result_bytes: int) -> Response:
    try:
        if isinstance(request, CountPagesRequest):
            return Counted(count_pages(Path(request.source)))
        if isinstance(request, WordsRequest):
            return Words(page_words(Path(request.source)))
        if isinstance(request, MarkdownCutRequest):
            return _markdown(request, max_result_bytes)
        if isinstance(request, TextCutRequest):
            text = _text(request.source, max_result_bytes)
            parts, over = cut_text(text, request.kind, Cut(request.cut), request.size)
            return MarkdownParts(parts, over)
        if isinstance(request, XlsxCutRequest):
            return FileParts(cut_xlsx(Path(request.source), request.parts))
        if isinstance(request, ReadTextRequest):
            # Merge's Markdown, read as it is, passes the same door (audit v4, B2-02).
            return TextRead(safe_output(_text(request.source, max_result_bytes))[0])
        if isinstance(request, MergePdfRequest):
            data = merge_pdfs([Path(source) for source in request.sources])
        else:
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
