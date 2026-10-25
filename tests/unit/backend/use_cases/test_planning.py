import shutil
import zipfile
from pathlib import Path

import pytest
from support import DOCUMENTS_DIR

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.limits import MIB, Limits
from clearmd.backend.schemas.models import Detection, DetectionMethod, InputProblem
from clearmd.backend.use_cases.planning import build_plan


class TableDetector:
    """Detects .pdf, .txt and .docx by extension, nothing else."""

    def detect(self, path: Path) -> Detection | None:
        table = {".pdf": FormatId.PDF, ".txt": FormatId.TXT, ".docx": FormatId.DOCX}
        found = table.get(path.suffix)
        return Detection(found, DetectionMethod.EXTENSION) if found else None


def test_a_supported_file_is_planned(tmp_path: Path) -> None:
    source = tmp_path / "report.pdf"
    source.write_bytes(b"%PDF")
    plan = build_plan([source], detector=TableDetector(), limits=Limits())
    (item,) = plan.conversions
    assert item.source == source
    assert item.target == tmp_path / "ClearMD_Output" / "OutputMD" / "report.md"
    assert not item.exists


def test_an_existing_output_is_marked(tmp_path: Path) -> None:
    source = tmp_path / "report.pdf"
    source.write_bytes(b"%PDF")
    target = tmp_path / "ClearMD_Output" / "OutputMD" / "report.md"
    target.parent.mkdir(parents=True)
    target.write_text("old", encoding="utf-8")
    (item,) = build_plan([source], detector=TableDetector(), limits=Limits()).conversions
    assert item.exists


def test_a_missing_input_is_an_input_error(tmp_path: Path) -> None:
    plan = build_plan([tmp_path / "nope.pdf"], detector=TableDetector(), limits=Limits())
    assert plan.is_empty
    assert [error.problem for error in plan.input_errors] == [InputProblem.NOT_FOUND]


def test_an_unsupported_file_is_skipped(tmp_path: Path) -> None:
    source = tmp_path / "notes.tex"
    source.write_text("x", encoding="utf-8")
    plan = build_plan([source], detector=TableDetector(), limits=Limits())
    assert [item.reason for item in plan.skipped] == [SkipReason.UNSUPPORTED_FORMAT]


def test_planning_writes_nothing(tmp_path: Path) -> None:
    source = tmp_path / "report.pdf"
    source.write_bytes(b"%PDF")
    build_plan([source], detector=TableDetector(), limits=Limits())
    assert sorted(path.name for path in tmp_path.iterdir()) == ["report.pdf"]


def test_a_folder_mirrors_its_structure_under_its_name(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "sub").mkdir(parents=True)
    (project / "top.pdf").write_bytes(b"%PDF")
    (project / "sub" / "inner.txt").write_text("x", encoding="utf-8")
    (project / "empty").mkdir()
    plan = build_plan([project], detector=TableDetector(), limits=Limits())
    root = tmp_path / "ClearMD_Output"
    assert [item.target for item in plan.conversions] == [
        root / "OutputMD" / "project" / "top.md",
        root / "OutputMD" / "project" / "sub" / "inner.md",
    ]
    assert {item.output_root for item in plan.conversions} == {root}


def test_no_recursive_planning(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "sub").mkdir(parents=True)
    (project / "top.pdf").write_bytes(b"%PDF")
    (project / "sub" / "inner.pdf").write_bytes(b"%PDF")
    plan = build_plan([project], recursive=False, detector=TableDetector(), limits=Limits())
    assert [item.source.name for item in plan.conversions] == ["top.pdf"]


def test_scanning_skips_reach_the_plan(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "notes.md").write_text("# hi", encoding="utf-8")
    plan = build_plan([project], detector=TableDetector(), limits=Limits())
    assert [item.reason for item in plan.skipped] == [SkipReason.ALREADY_MARKDOWN]


def test_an_unsafe_archive_is_skipped_while_planning(tmp_path: Path) -> None:
    bomb = tmp_path / "contract.docx"
    shutil.copyfile(DOCUMENTS_DIR / "zip_bomb.docx", bomb)
    plan = build_plan([bomb], detector=TableDetector(), limits=Limits())
    assert plan.is_empty
    assert [item.reason for item in plan.skipped] == [SkipReason.UNSAFE_ARCHIVE]


def test_the_cost_of_a_zip_document_counts_its_text_not_its_images(tmp_path: Path) -> None:
    path = tmp_path / "photos.docx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", "x" * MIB)
        archive.writestr(zipfile.ZipInfo("word/media/image1.png"), b"\x01" * (20 * MIB))
    limits = Limits()
    (item,) = build_plan([path], detector=TableDetector(), limits=limits).conversions
    assert item.cost == pytest.approx(limits.estimated_seconds(FormatId.DOCX, MIB))
