"""Feature 026 — Merge (spec/features/026_*/spec.md): real batches through the worker, the merged
file read back."""

import shutil
from pathlib import Path

import pypdfium2 as pdfium
import pytest
from support import DOCUMENTS_DIR
from support.pdf_builder import Text, build_pdf

from clearmd.backend.api import Into, plan_batch, run_batch
from clearmd.backend.schemas.errors import ErrorCode, SkipReason
from clearmd.backend.schemas.models import OutcomeStatus
from clearmd.frontend.cli import main
from clearmd.i18n import load_catalog


def pdf(folder: Path, name: str, pages: list[str]) -> Path:
    path = folder / name
    path.write_bytes(build_pdf([[Text(text, 700)] for text in pages]))
    return path


def merged(workdir: Path) -> list[Path]:
    return sorted((workdir / "ClearMD_Output" / "OutputUnif").iterdir())


def texts(path: Path) -> list[str]:
    document = pdfium.PdfDocument(path.read_bytes())
    try:
        return [page.get_textpage().get_text_range().strip() for page in document]
    finally:
        document.close()


def test_ac_01_into_one_markdown_in_the_lists_order(workdir: Path) -> None:
    second = pdf(workdir, "b.pdf", ["Beta page"])
    (workdir / "a.md").write_text("# Alpha\n\nalpha text\n", "utf-8")
    shutil.copyfile(DOCUMENTS_DIR / "sample.txt", workdir / "c.txt")
    paths = [workdir / "a.md", second, workdir / "c.txt"]
    report = run_batch(plan_batch(paths, merge=Into.MARKDOWN), overwrite=lambda item: True)
    assert [o.status for o in report.outcomes] == [OutcomeStatus.CONVERTED] * 3
    (result,) = merged(workdir)
    assert result.name.startswith("Merged ") and result.suffix == ".md"
    text = result.read_text("utf-8")
    markers = ["<!-- ClearMD: a.md -->", "<!-- ClearMD: b.pdf -->", "<!-- ClearMD: c.txt -->"]
    positions = [text.index(marker) for marker in markers]
    assert positions == sorted(positions)  # the list's order, not the cost's
    assert text.startswith("<!-- ClearMD: a.md -->\n\n# Alpha\n\nalpha text\n\n")  # as it is
    assert "Beta page" in text


def test_ac_01_the_name_is_in_the_users_language(workdir: Path) -> None:
    paths = [pdf(workdir, "a.pdf", ["A"]), pdf(workdir, "b.pdf", ["B"])]
    run_batch(plan_batch(paths, merge=Into.MARKDOWN), overwrite=lambda i: True, language="es")
    assert merged(workdir)[0].name.startswith("Unidos ")


def test_ac_02_into_one_pdf_with_every_page_in_order(workdir: Path) -> None:
    paths = [pdf(workdir, "a.pdf", ["A1", "A2"]), pdf(workdir, "b.pdf", ["B1"])]
    shutil.copyfile(DOCUMENTS_DIR / "sample.docx", workdir / "c.docx")
    plan = plan_batch([*paths, workdir / "c.docx"], merge=Into.PDF)
    assert [item.reason for item in plan.skipped] == [SkipReason.NOT_FOR_PDF_MERGE]
    run_batch(plan, overwrite=lambda item: True)
    (result,) = merged(workdir)
    assert result.suffix == ".pdf" and texts(result) == ["A1", "A2", "B1"]


def test_ac_03_a_failing_document_is_left_out_and_the_rest_merged(workdir: Path) -> None:
    shutil.copyfile(DOCUMENTS_DIR / "corrupt.pdf", workdir / "b.pdf")
    paths = [pdf(workdir, "a.pdf", ["A"]), workdir / "b.pdf", pdf(workdir, "c.pdf", ["C"])]
    report = run_batch(plan_batch(paths, merge=Into.PDF), overwrite=lambda item: True)
    statuses = {o.item.source.name: o.status for o in report.outcomes}
    assert statuses == {
        "a.pdf": OutcomeStatus.CONVERTED,
        "b.pdf": OutcomeStatus.FAILED,
        "c.pdf": OutcomeStatus.CONVERTED,
    }
    assert texts(merged(workdir)[0]) == ["A", "C"]


def test_ac_03_fewer_than_two_documents_write_nothing(workdir: Path) -> None:
    shutil.copyfile(DOCUMENTS_DIR / "corrupt.pdf", workdir / "b.pdf")
    paths = [pdf(workdir, "a.pdf", ["A"]), workdir / "b.pdf"]
    report = run_batch(plan_batch(paths, merge=Into.PDF), overwrite=lambda item: True)
    assert [o.error for o in report.outcomes] == [
        ErrorCode.NOTHING_TO_MERGE,
        ErrorCode.CORRUPT_FILE,
    ]
    assert not (workdir / "ClearMD_Output" / "OutputUnif").exists() or not merged(workdir)
    summary = (workdir / "ClearMD_Output" / "Resumen_ClearMD.md").read_text("utf-8")
    assert "Fewer than two documents could be merged" in summary


def test_ac_04_the_command_line_merges(workdir: Path) -> None:
    paths = [pdf(workdir, "b.pdf", ["B"]), pdf(workdir, "a.pdf", ["A"])]
    assert main([*map(str, paths), "--quiet", "--merge", "pdf"]) == 0
    assert texts(merged(workdir)[0]) == ["B", "A"]  # the order given
    summary = (workdir / "ClearMD_Output" / "Resumen_ClearMD.md").read_text("utf-8")
    assert "All 2 documents were merged into one file." in summary and "`OutputUnif/`" in summary


def test_ac_04_merge_cannot_go_with_a_split(workdir: Path) -> None:
    path = pdf(workdir, "a.pdf", ["A"])
    with pytest.raises(SystemExit) as stop:
        main([str(path), "--merge", "pdf", "--split-parts", "2"])
    assert stop.value.code == 2


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_06_texts_in_both_languages(language: str) -> None:
    catalog = load_catalog(language)
    for key in ("gui.home.merge", "gui.merge.title", "gui.settings.merge", "summary.merge_done"):
        assert catalog.text_template(key)
    merge = catalog.for_tool("merge")
    assert merge.text("gui.main.convert") == {"en": "Merge", "es": "Unir"}[language]
