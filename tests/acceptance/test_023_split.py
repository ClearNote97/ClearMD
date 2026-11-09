"""Feature 023 — Split a PDF (spec/features/023_*/spec.md): the cut, the parts written through the
real worker and read back page by page, what is kept, the command line and the summary."""

import shutil
from pathlib import Path

import pypdfium2 as pdfium
import pytest
from support import DOCUMENTS_DIR
from support.pdf_builder import Text, build_pdf

from clearmd.backend.api import Cut, Keep, SplitSpec, plan_batch, run_batch
from clearmd.backend.schemas.errors import ErrorCode, SkipReason
from clearmd.backend.schemas.models import BatchPlan, BatchReport, OutcomeStatus
from clearmd.backend.use_cases.split_ranges import page_ranges
from clearmd.frontend.cli import main


def book(folder: Path, pages: int, name: str = "book.pdf") -> Path:
    """A PDF whose page N says "Page N"."""
    path = folder / name
    path.write_bytes(build_pdf([[Text(f"Page {n}", 700)] for n in range(1, pages + 1)]))
    return path


def page_texts(path: Path) -> list[str]:
    document = pdfium.PdfDocument(path.read_bytes())
    try:
        return [page.get_textpage().get_text_range().strip() for page in document]
    finally:
        document.close()


def parts(workdir: Path, name: str = "book") -> list[str]:
    folder = workdir / "ClearMD_Output" / "OutputSep" / name
    return sorted(path.name for path in folder.iterdir())


def split(
    paths: list[Path], spec: SplitSpec, *, overwrite: bool = True
) -> tuple[BatchPlan, BatchReport]:
    plan = plan_batch(paths, split=spec)
    return plan, run_batch(plan, overwrite=lambda item: overwrite)


@pytest.mark.parametrize(
    ("pages", "cut", "size", "expected"),
    [
        (7, Cut.PARTS, 3, ((1, 3), (4, 5), (6, 7))),  # the first parts a page longer
        (6, Cut.PARTS, 3, ((1, 2), (3, 4), (5, 6))),
        (2, Cut.PARTS, 5, ((1, 1), (2, 2))),  # never more parts than pages
        (7, Cut.PAGES, 3, ((1, 3), (4, 6), (7, 7))),  # the last one shorter
        (3, Cut.PAGES, 10, ((1, 3),)),
        (0, Cut.PARTS, 2, ()),
    ],
)
def test_ac_01_the_cut_comes_from_the_page_count(
    pages: int, cut: Cut, size: int, expected: tuple[tuple[int, int], ...]
) -> None:
    ranges = page_ranges(pages, cut, size)
    assert ranges == expected
    assert all(first <= last for first, last in ranges)  # never an empty part


def test_ac_02_each_part_holds_its_pages_in_order_and_the_source_stays(workdir: Path) -> None:
    source = book(workdir, 5)
    before = source.read_bytes()
    _, report = split([source], SplitSpec(Cut.PAGES, 2, Keep.PDF))
    assert [outcome.parts for outcome in report.outcomes] == [3]
    assert parts(workdir) == [
        "book - part 1 of 3.pdf",
        "book - part 2 of 3.pdf",
        "book - part 3 of 3.pdf",
    ]
    folder = workdir / "ClearMD_Output" / "OutputSep" / "book"
    texts = [page_texts(folder / name) for name in parts(workdir)]
    assert texts == [["Page 1", "Page 2"], ["Page 3", "Page 4"], ["Page 5"]]
    assert source.read_bytes() == before


def test_ac_02_the_parts_are_named_in_spanish_too(workdir: Path) -> None:
    source = book(workdir, 2)
    plan = plan_batch([source], split=SplitSpec(Cut.PARTS, 2, Keep.PDF))
    run_batch(plan, overwrite=lambda item: True, language="es")
    assert parts(workdir) == ["book - parte 1 de 2.pdf", "book - parte 2 de 2.pdf"]


@pytest.mark.parametrize(
    ("keep", "suffixes"),
    [(Keep.PDF, {".pdf"}), (Keep.MARKDOWN, {".md"}), (Keep.BOTH, {".pdf", ".md"})],
)
def test_ac_03_the_user_chooses_what_to_keep(workdir: Path, keep: Keep, suffixes: set[str]) -> None:
    source = book(workdir, 4)
    split([source], SplitSpec(Cut.PARTS, 2, keep))
    names = parts(workdir)
    assert {Path(name).suffix for name in names} == suffixes
    assert len(names) == 2 * len(suffixes)
    if keep.markdown:
        first = workdir / "ClearMD_Output" / "OutputSep" / "book" / "book - part 1 of 2.md"
        text = first.read_text("utf-8")
        assert "Page 1" in text and "Page 2" in text and "Page 3" not in text


def test_ac_04_a_file_that_is_not_a_pdf_is_left_out_with_what_to_do(workdir: Path) -> None:
    shutil.copyfile(DOCUMENTS_DIR / "sample.docx", workdir / "notes.docx")
    plan = plan_batch([workdir / "notes.docx"], split=SplitSpec(Cut.PARTS, 2))
    assert plan.is_empty
    assert [item.reason for item in plan.skipped] == [SkipReason.NOT_SPLITTABLE]


def test_ac_04_a_damaged_or_locked_pdf_fails_alone(workdir: Path) -> None:
    for name in ("corrupt.pdf", "encrypted.pdf"):
        shutil.copyfile(DOCUMENTS_DIR / name, workdir / name)
    good = book(workdir, 2)
    paths = [workdir / "corrupt.pdf", workdir / "encrypted.pdf", good]
    _, report = split(paths, SplitSpec(Cut.PARTS, 2, Keep.PDF))
    by_name = {o.item.source.name: o for o in report.outcomes}
    assert by_name["corrupt.pdf"].error is ErrorCode.CORRUPT_FILE
    assert by_name["encrypted.pdf"].error is ErrorCode.PASSWORD_PROTECTED
    assert by_name["book.pdf"].status is OutcomeStatus.CONVERTED


def test_ac_05_overwrite_replaces_only_the_parts_of_the_earlier_cut(workdir: Path) -> None:
    source = book(workdir, 6)
    split([source], SplitSpec(Cut.PARTS, 3, Keep.PDF))
    mine = workdir / "ClearMD_Output" / "OutputSep" / "book" / "my notes.txt"
    mine.write_text("mine", "utf-8")
    split([source], SplitSpec(Cut.PARTS, 2, Keep.PDF))
    assert parts(workdir) == ["book - part 1 of 2.pdf", "book - part 2 of 2.pdf", "my notes.txt"]


def test_ac_05_keep_leaves_the_earlier_parts(workdir: Path) -> None:
    source = book(workdir, 4)
    split([source], SplitSpec(Cut.PARTS, 2, Keep.PDF))
    plan, report = split([source], SplitSpec(Cut.PARTS, 4, Keep.PDF), overwrite=False)
    assert plan.conversions[0].exists
    assert [o.status for o in report.outcomes] == [OutcomeStatus.KEPT]
    assert len(parts(workdir)) == 2


def test_ac_06_the_command_line_splits(workdir: Path) -> None:
    source = book(workdir, 5)
    assert main([str(source), "--quiet", "--split-pages", "2", "--keep", "markdown"]) == 0
    assert parts(workdir) == [f"book - part {n} of 3.md" for n in (1, 2, 3)]
    assert main([str(source), "--quiet", "--overwrite", "--split-parts", "5"]) == 0
    assert len(parts(workdir)) == 10  # both, by default


@pytest.mark.parametrize(
    "arguments",
    [
        ["--split-parts", "2", "--split-pages", "2"],  # the two cuts together
        ["--split-parts", "1"],  # fewer than 2 parts
        ["--split-pages", "0"],
        ["--keep", "pdf"],  # --keep without a cut
    ],
)
def test_ac_06_wrong_split_arguments_are_refused(workdir: Path, arguments: list[str]) -> None:
    source = book(workdir, 2)
    with pytest.raises(SystemExit) as stop:
        main([str(source), *arguments])
    assert stop.value.code == 2
    assert not (workdir / "ClearMD_Output").exists()


def test_ac_07_the_summary_says_into_how_many_parts_and_where(workdir: Path) -> None:
    source = book(workdir, 3)
    assert main([str(source), "--quiet", "--split-parts", "3", "--summary-pdf"]) == 0
    summary = (workdir / "ClearMD_Output" / "Resumen_ClearMD.md").read_text("utf-8")
    assert "The document was split." in summary
    assert "`OutputSep/`" in summary and "`book/ (3 parts)`" in summary
    pdf = page_texts(workdir / "ClearMD_Output" / "Resumen_ClearMD.pdf")
    assert any("OutputSep/" in page and "book/ (3 parts)" in page for page in pdf)
