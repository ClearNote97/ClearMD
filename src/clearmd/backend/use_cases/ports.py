"""The ports the use cases need; ``backend/services`` implements them (ADR-0001, ADR-0014)."""

from datetime import datetime
from pathlib import Path
from typing import Protocol

from clearmd.backend.schemas.models import ConversionResult, Detection, PlannedConversion
from clearmd.backend.use_cases.cancel import CancelToken


class FormatDetector(Protocol):
    def detect(self, path: Path) -> Detection | None:
        """The format of ``path``, or ``None`` when it is not supported."""
        ...


class ConversionRunner(Protocol):
    def convert(self, item: PlannedConversion, cancel: CancelToken) -> ConversionResult:
        """The Markdown of ``item.source``, and its conversion notes.

        Raises ``ConversionError`` for a known failure and ``Cancelled`` when ``cancel`` is set.
        """
        ...

    def warm_up(self, cancel: CancelToken) -> None:
        """Get ready before the first file, so its time does not include any start-up."""
        ...

    def close(self) -> None: ...


class PageCutter(Protocol):
    """A PDF's pages, counted and copied whole into a new PDF (Split, feature 023)."""

    def count_pages(self, item: PlannedConversion, cancel: CancelToken) -> int: ...

    def cut(self, item: PlannedConversion, first: int, last: int, cancel: CancelToken) -> bytes:
        """Raises ``ConversionError`` for a known failure and ``Cancelled`` when ``cancel`` is
        set."""
        ...

    def page_words(self, item: PlannedConversion, cancel: CancelToken) -> tuple[int, ...]:
        """The words on each page (feature 024)."""
        ...

    def markdown_parts(
        self, item: PlannedConversion, cut: str, size: int, cancel: CancelToken
    ) -> tuple[tuple[str, ...], tuple[int, ...]]:
        """A Markdown file's parts, and which ones are over the size (feature 024)."""
        ...

    def read_text(self, item: PlannedConversion, cancel: CancelToken) -> str:
        """A Markdown file's text, as it is (Merge, feature 026)."""
        ...

    def merge_pdfs(self, items: list[PlannedConversion], cancel: CancelToken) -> bytes:
        """One PDF with every page of ``items``, whole and in order (feature 026)."""
        ...


class Clock(Protocol):
    def now(self) -> datetime: ...
