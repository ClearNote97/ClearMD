"""Smoke test: the benchmark's generators and measurement still work, at tiny sizes."""

import random
import zipfile
from pathlib import Path

import pytest
from benchlib.cases import CASES, Case
from benchlib.common import MIB, SEED
from benchlib.measure import run


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.kind)
def test_every_generator_builds_a_document_of_about_the_requested_size(
    case: Case, tmp_path: Path
) -> None:
    size = 64 * 1024 if case.kind != "docx_images" else 2 * MIB
    path = tmp_path / f"{case.kind}{case.extension}"
    case.build(path, size, random.Random(SEED))
    built = path.stat().st_size
    if case.extension == ".odt":  # what costs is the text inside, not the compressed file
        with zipfile.ZipFile(path) as archive:
            built = archive.getinfo("content.xml").file_size
    assert size * 0.5 <= built <= size * 3


def test_one_measurement_end_to_end(tmp_path: Path) -> None:
    case = next(case for case in CASES if case.kind == "docx_text")
    tiny = Case(case.kind, case.extension, case.build, (0.05,))
    (row,) = run(
        [tiny],
        tmp_path,
        memory_cap=2048 * MIB,
        timeout=120,
        slow_after=60,
        log=lambda _: None,
    )
    assert row.result["ok"], row.result
    assert row.result["peak_mib"] > row.result["baseline_mib"] > 0
    assert row.archive is not None and row.archive["total_ratio"] > 1


@pytest.mark.parametrize("kind", ["tex", "tex_macros", "odt"])
def test_own_converter_cases_measure_real_work_on_the_supported_subset(
    kind: str, tmp_path: Path
) -> None:
    case = next(case for case in CASES if case.kind == kind)
    assert case.engine in {"tex", "odt"}
    tiny = Case(case.kind, case.extension, case.build, (0.05,), case.engine)
    (row,) = run(
        [tiny],
        tmp_path,
        memory_cap=2048 * MIB,
        timeout=120,
        slow_after=60,
        log=lambda _: None,
    )
    assert row.result["ok"], row.result
    assert row.result["notes"] == []  # all of it is real work: nothing left as written
    assert row.result["markdown_mib"] > 0
