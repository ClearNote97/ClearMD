from pathlib import Path

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.services.detection.chain import ChainDetector


class Fixed:
    def __init__(self, answer: Detection | None) -> None:
        self.answer = answer
        self.calls = 0

    def detect(self, path: Path) -> Detection | None:
        self.calls += 1
        return self.answer


def test_the_first_answer_wins_and_later_detectors_are_not_asked() -> None:
    first = Fixed(Detection(FormatId.PDF, DetectionMethod.EXTENSION))
    second = Fixed(Detection(FormatId.DOCX, DetectionMethod.CONTENT))
    assert ChainDetector(first, second).detect(Path("x.pdf")) == first.answer
    assert second.calls == 0


def test_falls_through_to_the_next_detector() -> None:
    content = Detection(FormatId.DOCX, DetectionMethod.CONTENT)
    assert ChainDetector(Fixed(None), Fixed(content)).detect(Path("scan")) == content


def test_nobody_knows() -> None:
    assert ChainDetector(Fixed(None), Fixed(None)).detect(Path("x")) is None
