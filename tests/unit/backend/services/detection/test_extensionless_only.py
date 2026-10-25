from pathlib import Path

import pytest

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.services.detection.content_policy import ExtensionlessOnly


class Answers:
    def __init__(self, format_id: FormatId) -> None:
        self.detection = Detection(format_id, DetectionMethod.CONTENT)
        self.calls = 0

    def detect(self, path: Path) -> Detection | None:
        self.calls += 1
        return self.detection


@pytest.mark.parametrize(("name", "format_id"), [("README", FormatId.TXT), ("scan", FormatId.DOCX)])
def test_files_without_extension_are_detected_by_content(name: str, format_id: FormatId) -> None:
    detection = ExtensionlessOnly(Answers(format_id)).detect(Path(name))
    assert detection is not None and detection.format is format_id


@pytest.mark.parametrize("name", ["paper.tex", "server.log", "report.dat"])
def test_an_unknown_extension_is_never_looked_into(name: str) -> None:
    content = Answers(FormatId.DOCX)
    assert ExtensionlessOnly(content).detect(Path(name)) is None
    assert content.calls == 0
