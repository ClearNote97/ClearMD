"""Smoke test: the benchmark's generators and measurement still work, at tiny sizes."""

import random
from pathlib import Path

import pytest
import run_benchmark as bench


@pytest.mark.parametrize("case", bench.CASES, ids=lambda case: case.kind)
def test_every_generator_builds_a_document_of_about_the_requested_size(
    case: bench.Case, tmp_path: Path
) -> None:
    size = 64 * 1024 if case.kind != "docx_images" else 2 * bench.MIB
    path = tmp_path / f"{case.kind}{case.extension}"
    case.build(path, size, random.Random(bench.SEED))
    assert size * 0.5 <= path.stat().st_size <= size * 3


def test_one_measurement_end_to_end(tmp_path: Path) -> None:
    case = next(case for case in bench.CASES if case.kind == "docx_text")
    tiny = bench.Case(case.kind, case.extension, case.build, (0.05,))
    (row,) = bench.run(
        [tiny],
        tmp_path,
        memory_cap=2048 * bench.MIB,
        timeout=120,
        slow_after=60,
        log=lambda _: None,
    )
    assert row.result["ok"], row.result
    assert row.result["peak_mib"] > row.result["baseline_mib"] > 0
    assert row.archive is not None and row.archive["total_ratio"] > 1


@pytest.mark.parametrize("kind", ["tex", "tex_macros"])
def test_the_tex_cases_measure_clearmds_converter_on_the_supported_subset(
    kind: str, tmp_path: Path
) -> None:
    case = next(case for case in bench.CASES if case.kind == kind)
    assert case.engine == "tex"
    tiny = bench.Case(case.kind, case.extension, case.build, (0.05,), case.engine)
    (row,) = bench.run(
        [tiny],
        tmp_path,
        memory_cap=2048 * bench.MIB,
        timeout=120,
        slow_after=60,
        log=lambda _: None,
    )
    assert row.result["ok"], row.result
    assert row.result["notes"] == []  # all of it is real work: nothing left as written
    assert row.result["markdown_mib"] > 0
