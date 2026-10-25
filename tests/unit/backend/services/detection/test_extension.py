from pathlib import Path

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import DetectionMethod
from clearmd.backend.services.detection.extension import ExtensionDetector


def test_known_extension_is_detected_without_reading_the_file() -> None:
    detection = ExtensionDetector().detect(Path("/does/not/exist/Report.PDF"))
    assert detection is not None
    assert detection.format is FormatId.PDF
    assert detection.method is DetectionMethod.EXTENSION


def test_unknown_or_missing_extension_is_not_detected() -> None:
    assert ExtensionDetector().detect(Path("refs.bib")) is None
    assert ExtensionDetector().detect(Path("scan")) is None
