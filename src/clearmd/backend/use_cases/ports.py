"""The ports the use cases need; ``backend/services`` implements them (ADR-0001, ADR-0014)."""

from datetime import datetime
from pathlib import Path
from typing import Protocol

from clearmd.backend.schemas.models import Detection, PlannedConversion
from clearmd.backend.use_cases.cancel import CancelToken


class FormatDetector(Protocol):
    def detect(self, path: Path) -> Detection | None:
        """The format of ``path``, or ``None`` when it is not supported."""
        ...


class ConversionRunner(Protocol):
    def convert(self, item: PlannedConversion, cancel: CancelToken) -> str:
        """The Markdown of ``item.source``.

        Raises ``ConversionError`` for a known failure and ``Cancelled`` when ``cancel`` is set.
        """
        ...

    def close(self) -> None: ...


class Clock(Protocol):
    def now(self) -> datetime: ...
