"""magika's real labels, verified on the fixtures (T10). Runs magika in this test process only."""

import shutil
from pathlib import Path

import pytest
from support import DOCUMENTS_DIR

from clearmd.backend.schemas.formats import FormatId, format_for_extension
from clearmd.backend.schemas.models import DetectionMethod
from clearmd.backend.services.detection.content import MagikaDetector


@pytest.fixture(scope="module")
def detector() -> MagikaDetector:
    return MagikaDetector()


SAMPLES = sorted(p.name for p in DOCUMENTS_DIR.glob("sample.*"))


@pytest.mark.parametrize("name", SAMPLES)
def test_every_supported_format_is_recognized_by_content(
    detector: MagikaDetector, name: str
) -> None:
    detection = detector.detect(DOCUMENTS_DIR / name)
    assert detection is not None
    assert detection.format is format_for_extension(Path(name).suffix)
    assert detection.method is DetectionMethod.CONTENT


def test_a_docx_without_extension_is_a_docx(detector: MagikaDetector) -> None:
    detection = detector.detect(DOCUMENTS_DIR / "docx_without_extension")
    assert detection is not None and detection.format is FormatId.DOCX


def test_text_with_an_unknown_extension_is_plain_text(
    detector: MagikaDetector, tmp_path: Path
) -> None:
    path = tmp_path / "notes.dat"
    shutil.copyfile(DOCUMENTS_DIR / "sample.txt", path)
    detection = detector.detect(path)
    assert detection is not None and detection.format is FormatId.TXT


def test_unrecognized_content_is_not_detected(detector: MagikaDetector, tmp_path: Path) -> None:
    assert detector.detect(DOCUMENTS_DIR / "corrupt.pdf") is None
    script = tmp_path / "tool"
    script.write_text("import sys\n\ndef main():\n    print(sys.argv)\n", encoding="utf-8")
    assert detector.detect(script) is None


def test_odt_without_extension_is_detected_by_content(detector: MagikaDetector) -> None:
    from support import ODT_DIR

    detection = detector.detect(ODT_DIR / "no_extension_odt")
    assert detection is not None and detection.format is FormatId.ODT


def test_latex_without_extension_is_detected_by_content(detector: MagikaDetector) -> None:
    from support import TEX_DIR

    detection = detector.detect(TEX_DIR / "no_extension_latex")
    assert detection is not None and detection.format is FormatId.TEX
