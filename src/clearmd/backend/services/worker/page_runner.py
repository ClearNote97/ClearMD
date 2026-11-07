"""Split's page jobs through the worker (features 023, 024, ADR-0044): a ``PageCutter`` over the
same ``WorkerRunner``, so they share its process and its limits."""

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.models import PlannedConversion
from clearmd.backend.services.worker.protocol import (
    Counted,
    CountPagesRequest,
    CutDone,
    CutRequest,
    MarkdownCutRequest,
    MarkdownParts,
    Request,
    Response,
    Words,
    WordsRequest,
)
from clearmd.backend.services.worker.supervisor import WorkerRunner
from clearmd.backend.use_cases.cancel import CancelToken


class PageRunner:
    def __init__(self, runner: WorkerRunner) -> None:
        self._runner = runner

    def count_pages(self, item: PlannedConversion, cancel: CancelToken) -> int:
        return self._expect(CountPagesRequest(str(item.source)), Counted, cancel).pages

    def cut(self, item: PlannedConversion, first: int, last: int, cancel: CancelToken) -> bytes:
        return self._expect(CutRequest(str(item.source), first, last), CutDone, cancel).data

    def page_words(self, item: PlannedConversion, cancel: CancelToken) -> tuple[int, ...]:
        return self._expect(WordsRequest(str(item.source)), Words, cancel).per_page

    def markdown_parts(
        self, item: PlannedConversion, cut: str, size: int, cancel: CancelToken
    ) -> tuple[tuple[str, ...], tuple[int, ...]]:
        request = MarkdownCutRequest(str(item.source), cut, size)
        found = self._expect(request, MarkdownParts, cancel)
        return found.parts, found.over

    def _expect[T: Response](self, request: Request, kind: type[T], cancel: CancelToken) -> T:
        response = self._runner.job(request, cancel)
        if not isinstance(response, kind):
            raise ConversionError(ErrorCode.CONVERSION_FAILED, f"unexpected reply {response!r}")
        return response
