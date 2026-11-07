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


class Clock(Protocol):
    def now(self) -> datetime: ...
