"""Chain detectors from the cheapest to the most expensive; the first answer wins (ADR-0010)."""

from pathlib import Path

from clearmd.backend.schemas.models import Detection
from clearmd.backend.use_cases.ports import FormatDetector


class ChainDetector:
    def __init__(self, *detectors: FormatDetector) -> None:
        self._detectors = detectors

    def detect(self, path: Path) -> Detection | None:
        for detector in self._detectors:
            detection = detector.detect(path)
            if detection is not None:
                return detection
        return None
