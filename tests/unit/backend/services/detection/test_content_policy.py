from pathlib import Path

import pytest

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.services.detection.content_policy import DocumentsOnlyWithExtension


class Answers:
    def __init__(self, format_id: FormatId) -> None:
        self.detection = Detection(format_id, DetectionMethod.CONTENT)

    def detect(self, path: Path) -> Detection | None:
        return self.detection


@pytest.mark.parametrize("name", ["README", "scan"])
def test_plain_text_is_accepted_for_files_without_extension(name: str) -> None:
    assert DocumentsOnlyWithExtension(Answers(FormatId.TXT)).detect(Path(name)) is not None


@pytest.mark.parametrize("name", ["paper.tex", "server.log", "config.yaml"])
def test_plain_text_with_an_unknown_extension_is_not_converted(name: str) -> None:
    assert DocumentsOnlyWithExtension(Answers(FormatId.TXT)).detect(Path(name)) is None


def test_a_real_document_with_an_unknown_extension_is_accepted() -> None:
    detection = DocumentsOnlyWithExtension(Answers(FormatId.DOCX)).detect(Path("report.dat"))
    assert detection is not None and detection.format is FormatId.DOCX
