"""Feature 027 — Split takes text, CSV and Excel (spec/features/027_*/spec.md): real batches
through the worker, the parts read back."""

from pathlib import Path

import openpyxl
import pytest
from openpyxl.styles import Font

from clearmd.backend.api import Cut, Keep, SplitSpec, plan_batch, run_batch
from clearmd.backend.schemas.errors import SkipReason
from clearmd.frontend.cli import main
from clearmd.i18n import load_catalog

TEXT = "".join(f"line {n} with some words\n" for n in range(1, 13))
CSV = 'name,note\nana,"two\nlines"\nbeto,plain\ncata,"x, y"\ndani,last\n'


def parts_of(workdir: Path, name: str) -> list[Path]:
    return sorted((workdir / "ClearMD_Output" / "OutputSep" / name).iterdir())


def split(paths: list[Path], spec: SplitSpec) -> None:
    run_batch(plan_batch(paths, split=spec), overwrite=lambda item: True)


def test_ac_01_text_is_cut_at_line_breaks_and_put_back_is_the_file(workdir: Path) -> None:
    (workdir / "notes.txt").write_text(TEXT, "utf-8")
    split([workdir / "notes.txt"], SplitSpec(Cut.PARTS, 3, Keep.PDF))
    parts = parts_of(workdir, "notes")
    assert [path.suffix for path in parts] == [".txt"] * 3
    assert "".join(path.read_text("utf-8") for path in parts) == TEXT


def test_ac_01_and_02_every_n_pages_leaves_text_and_csv_out(workdir: Path) -> None:
    (workdir / "a.txt").write_text(TEXT, "utf-8")
    (workdir / "b.csv").write_text(CSV, "utf-8")
    plan = plan_batch([workdir / "a.txt", workdir / "b.csv"], split=SplitSpec(Cut.PAGES, 2))
    assert {item.reason for item in plan.skipped} == {SkipReason.NO_PAGES_TO_CUT}


def test_ac_02_every_csv_part_starts_with_the_header_and_keeps_quoted_rows(
    workdir: Path,
) -> None:
    (workdir / "people.csv").write_text(CSV, "utf-8")
    split([workdir / "people.csv"], SplitSpec(Cut.PARTS, 2, Keep.PDF))
    texts = [path.read_text("utf-8") for path in parts_of(workdir, "people")]
    assert len(texts) == 2 and all(text.startswith("name,note\n") for text in texts)
    rows = "".join(text.removeprefix("name,note\n") for text in texts)
    assert rows == CSV.removeprefix("name,note\n")  # the rows, in order, never cut inside
    assert 'ana,"two\nlines"\n' in texts[0]


def workbook(path: Path) -> None:
    book = openpyxl.Workbook()
    first = book.active
    assert first is not None
    first.title = "Jan"
    first["A1"] = "Total"
    first["A1"].font = Font(bold=True)
    first.column_dimensions["A"].width = 30
    for name in ("Feb", "Mar"):
        book.create_sheet(name)["A1"] = name
    book.save(path)


def test_ac_03_excel_is_cut_by_whole_sheets_keeping_their_formats(workdir: Path) -> None:
    workbook(workdir / "year.xlsx")
    split([workdir / "year.xlsx"], SplitSpec(Cut.PARTS, 5, Keep.PDF))
    parts = parts_of(workdir, "year")
    sheets = [openpyxl.load_workbook(path).sheetnames for path in parts]
    assert sheets == [["Jan"], ["Feb"], ["Mar"]]  # fewer sheets than parts: one each
    first = openpyxl.load_workbook(parts[0])["Jan"]
    assert first["A1"].font.bold and first.column_dimensions["A"].width == 30


@pytest.mark.parametrize("cut", [Cut.PAGES, Cut.WORDS])
def test_ac_03_excel_takes_only_into_n_parts(workdir: Path, cut: Cut) -> None:
    workbook(workdir / "year.xlsx")
    size = 2 if cut is Cut.PAGES else 1000
    plan = plan_batch([workdir / "year.xlsx"], split=SplitSpec(cut, size))
    assert [item.reason for item in plan.skipped] == [SkipReason.CUT_BY_SHEETS]


def test_ac_04_their_markdown_too(workdir: Path) -> None:
    (workdir / "people.csv").write_text(CSV, "utf-8")
    split([workdir / "people.csv"], SplitSpec(Cut.PARTS, 2, Keep.BOTH))
    suffixes = sorted(path.suffix for path in parts_of(workdir, "people"))
    assert suffixes == [".csv", ".csv", ".md", ".md"]


def test_ac_05_the_command_line_and_the_texts(workdir: Path) -> None:
    (workdir / "notes.txt").write_text(TEXT, "utf-8")
    assert main([str(workdir / "notes.txt"), "--quiet", "--split-words", "500"]) == 0
    for language in ("en", "es"):
        body = load_catalog(language).text("gui.home.split_body")
        assert "CSV" in body and "Excel" in body
