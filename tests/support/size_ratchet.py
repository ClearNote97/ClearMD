"""The files and classes over the size rule when refactor R01 began (ADR-0039), with their size
then. Each may only shrink; once under the limit its entry must go. Empty at the end of R01."""

FILES: dict[str, int] = {  # path -> lines (over 250)
    "src/clearmd/backend/services/conversion/html/render.py": 485,
    "src/clearmd/backend/services/summary/pdf_report.py": 400,
    "tests/acceptance/test_001_batch_conversion.py": 763,
    "tests/acceptance/test_005_ttk_gui.py": 620,
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
    "tests/unit/frontend/presenter/test_presenter.py": 885,
    "tests/unit/frontend/ttk/test_main_window.py": 892,
}

CLASSES: dict[str, int] = {  # "path::Class" -> lines (over 150)
    "src/clearmd/backend/services/conversion/html/render.py::ArticleRenderer": 303,
    "src/clearmd/backend/services/summary/pdf_report.py::PdfReport": 155,
    "src/clearmd/backend/services/worker/supervisor.py::WorkerRunner": 159,
}
# The GUIs' entry files (≤ 40 lines) that are still whole windows.
ENTRY_FILES: dict[str, int] = {}
