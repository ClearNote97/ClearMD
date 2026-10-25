"""Detection by file extension: free, runs in the interface's process."""

from pathlib import Path

from clearmd.backend.schemas.formats import format_for_extension
from clearmd.backend.schemas.models import Detection, DetectionMethod


class ExtensionDetector:
    def detect(self, path: Path) -> Detection | None:
        format_id = format_for_extension(path.suffix)
        return Detection(format_id, DetectionMethod.EXTENSION) if format_id is not None else None
