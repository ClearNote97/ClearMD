"""Feature 010 — one test per acceptance criterion (spec/features/010_*/spec.md). The executables
themselves are built and checked on CI (feature 006: packaging/check_executables.sh)."""

import shutil
from pathlib import Path

import pytest
from support import DOCUMENTS_DIR, ODT_DIR, TEX_DIR

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.services.conversion.registry import build_registry
from clearmd.backend.services.conversion.xlsx import XlsxConverter
from clearmd.backend.services.detection.content import SignatureDetector

ROOT = Path(__file__).resolve().parents[2]


SAMPLES = [
    (DOCUMENTS_DIR / f"sample.{format_id.value}", format_id)
    for format_id in FormatId
    if (DOCUMENTS_DIR / f"sample.{format_id.value}").is_file()
] + [(ODT_DIR / "no_extension_odt", FormatId.ODT), (TEX_DIR / "no_extension_latex", FormatId.TEX)]


@pytest.mark.parametrize(("fixture", "format_id"), SAMPLES)
def test_ac_01_every_format_is_recognised_without_its_extension(
    tmp_path: Path, fixture: Path, format_id: FormatId
) -> None:
    unnamed = tmp_path / "escaneado"
    shutil.copyfile(fixture, unnamed)
    assert build_registry().detect_content(unnamed) == Detection(format_id, DetectionMethod.CONTENT)


def test_ac_01_a_program_or_unknown_data_is_unsupported(tmp_path: Path) -> None:
    script = tmp_path / "tool"
    script.write_text("#!/bin/sh\necho hello\n", encoding="utf-8")
    data = tmp_path / "blob"
    data.write_bytes(bytes(range(256)) * 4)
    assert SignatureDetector().detect(script) is None and SignatureDetector().detect(data) is None


def test_ac_02_excel_is_clearmds_own_and_an_encrypted_workbook_is_locked(tmp_path: Path) -> None:
    assert isinstance(build_registry().for_format(FormatId.XLSX), XlsxConverter)
    detection = Detection(FormatId.XLSX, DetectionMethod.EXTENSION)
    result = XlsxConverter().convert(DOCUMENTS_DIR / "sample.xlsx", detection, tmp_path / "x.md")
    assert "## Data" in result.markdown and "| fixture-xlsx | 1 |" in result.markdown
    locked = tmp_path / "locked.xlsx"
    locked.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 600)
    with pytest.raises(ConversionError) as raised:
        XlsxConverter().convert(locked, detection, tmp_path / "l.md")
    assert raised.value.code is ErrorCode.PASSWORD_PROTECTED


def test_ac_03_the_heavy_libraries_are_left_out_and_the_notices_say_only_what_ships() -> None:
    spec = (ROOT / "packaging" / "clearmd.spec").read_text(encoding="utf-8")
    assert 'HEAVY = ["magika", "onnxruntime", "numpy", "pandas"]' in spec
    assert 'BABEL_KEPT = ("root.dat", "en.dat", "es.dat")' in spec and "no_magika.py" in spec
    notices = (ROOT / "packaging" / "notices.py").read_text(encoding="utf-8")
    assert all(name in notices for name in ('"magika"', '"onnxruntime"', '"numpy"', '"pandas"'))
    hook = (ROOT / "packaging" / "no_magika.py").read_text(encoding="utf-8")
    assert 'sys.modules.setdefault("magika"' in hook


def test_ac_04_the_executables_are_checked_by_a_real_batch_and_measured() -> None:
    check = (ROOT / "packaging" / "check_executables.sh").read_text(encoding="utf-8")
    assert "sample.xlsx" in check and "docx_without_extension" in check
    assert "MAX_MB=50" in check  # the Linux executable must stay under it
