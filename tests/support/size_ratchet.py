"""The files and classes over the size rule when refactor R01 began (ADR-0039), with their size
then. Each may only shrink; once under the limit its entry must go. Empty at the end of R01."""

FILES: dict[str, int] = {  # path -> lines (over 250)
    "tests/acceptance/test_001_batch_conversion.py": 763,
    "tests/benchmark/run_benchmark.py": 789,
    "tests/fixtures/build_fixtures.py": 1018,
    "tests/gui/make_assets.py": 318,
    "tests/unit/backend/services/conversion/images/test_images.py": 295,
    "tests/unit/backend/services/conversion/odt/test_render.py": 267,
    "tests/unit/backend/services/conversion/odt/test_review_code.py": 295,
    "tests/unit/backend/services/conversion/odt/test_verify_findings.py": 310,
    "tests/unit/backend/services/conversion/pdf/test_pdf_converter.py": 499,
    "tests/unit/backend/services/conversion/pdf/test_tables.py": 498,
    "tests/unit/backend/services/conversion/tex/test_review_findings.py": 636,
    "tests/unit/backend/services/summary/test_writer.py": 484,
    "tests/unit/backend/services/worker/test_supervisor.py": 261,
    "tests/unit/backend/use_cases/test_execution.py": 312,
}

CLASSES: dict[str, int] = {  # "path::Class" -> lines (over 150)
}
# The GUIs' entry files (≤ 40 lines) that are still whole windows.
ENTRY_FILES: dict[str, int] = {}
