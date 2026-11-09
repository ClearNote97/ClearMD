"""Feature 034 — Never lose or misreport work (spec/features/034_*/spec.md): real batches through
the worker, read back."""

import os
from pathlib import Path

import pytest
from support.pdf_builder import Text, build_pdf

from clearmd.backend.api import Cut, Into, Keep, SplitSpec, plan_batch, run_batch
from clearmd.backend.schemas.errors import ErrorCode, SkipReason
from clearmd.backend.schemas.models import OutcomeStatus
from clearmd.backend.services.conversion.csv_dialect import separator
from clearmd.backend.use_cases.output_files import sweep_temporary_files
from clearmd.frontend.presenter.screens.primary import primary_of
from clearmd.frontend.presenter.state import AppState, Tool
from clearmd.i18n import load_catalog

YES = lambda item: True  # noqa: E731


def book(folder: Path, pages: int, name: str = "book.pdf") -> Path:
    path = folder / name
    path.write_bytes(build_pdf([[Text(f"Page {n}", 700)] for n in range(1, pages + 1)]))
    return path


def listing(folder: Path) -> list[str]:
    return sorted(path.name for path in folder.iterdir())


def test_ac_01_a_failed_split_keeps_the_earlier_parts(workdir: Path) -> None:
    source = book(workdir, 6)
    run_batch(plan_batch([source], split=SplitSpec(Cut.PARTS, 2, Keep.PDF)), overwrite=YES)
    folder = workdir / "ClearMD_Output" / "OutputSep" / "book"
    before = {name: (folder / name).read_bytes() for name in listing(folder)}
    (folder / "book - part 3 of 3.pdf").mkdir()  # an obstacle where a new part must go
    report = run_batch(plan_batch([source], split=SplitSpec(Cut.PARTS, 3, Keep.PDF)), overwrite=YES)
    assert report.outcomes[0].status is OutcomeStatus.FAILED
    (folder / "book - part 3 of 3.pdf").rmdir()
    assert {name: (folder / name).read_bytes() for name in listing(folder)} == before


def test_ac_01_a_split_that_works_still_replaces_the_earlier_cut(workdir: Path) -> None:
    source = book(workdir, 6)
    run_batch(plan_batch([source], split=SplitSpec(Cut.PARTS, 3, Keep.PDF)), overwrite=YES)
    run_batch(plan_batch([source], split=SplitSpec(Cut.PARTS, 2, Keep.PDF)), overwrite=YES)
    folder = workdir / "ClearMD_Output" / "OutputSep" / "book"
    assert listing(folder) == ["book - part 1 of 2.pdf", "book - part 2 of 2.pdf"]


def test_ac_01_staged_parts_left_by_a_power_cut_are_swept(workdir: Path) -> None:
    folder = workdir / "ClearMD_Output" / "OutputSep" / "book"
    folder.mkdir(parents=True)
    (folder / ".book - part 1 of 2.clearmd-part.pdf").write_bytes(b"half")
    (folder / "mine.pdf").write_bytes(b"mine")
    sweep_temporary_files(workdir / "ClearMD_Output")
    assert listing(folder) == ["mine.pdf"]


def test_ac_02_a_second_merge_in_the_same_minute_gets_its_own_file(workdir: Path) -> None:
    for name in "abcd":
        (workdir / f"{name}.md").write_text(f"# {name}\n\n{name} text\n", "utf-8")
    first = plan_batch([workdir / "a.md", workdir / "b.md"], merge=Into.MARKDOWN)
    second = plan_batch([workdir / "c.md", workdir / "d.md"], merge=Into.MARKDOWN)
    assert first.merge and second.merge and first.merge.target == second.merge.target
    first_name = run_batch(first, overwrite=YES).outcomes[0].item.target.name
    report = run_batch(second, overwrite=YES)
    folder = workdir / "ClearMD_Output" / "OutputUnif"
    second_name = first_name.removesuffix(".md") + " (2).md"
    assert listing(folder) == sorted([first_name, second_name])
    assert "a text" in (folder / first_name).read_text("utf-8")
    assert "c text" in (folder / second_name).read_text("utf-8")
    assert report.outcomes[0].item.target.name == second_name  # the summary names the real file


def test_ac_02_each_merged_document_opens_with_a_visible_line(workdir: Path) -> None:
    for name in "ab":
        (workdir / f"{name}.md").write_text(f"{name} text\n", "utf-8")
    plan = plan_batch([workdir / "a.md", workdir / "b.md"], merge=Into.MARKDOWN)
    run_batch(plan, overwrite=YES, language="es")
    (merged,) = (workdir / "ClearMD_Output" / "OutputUnif").iterdir()
    text = merged.read_text("utf-8")
    assert "*Documento 1 de 2: a.md*" in text and "*Documento 2 de 2: b.md*" in text
    assert "\n---\n" in text and "<!-- ClearMD: b.md -->" in text


def test_ac_03_a_merge_with_one_good_document_leaves_its_summary(workdir: Path) -> None:
    good = book(workdir, 1, "good.pdf")
    broken = workdir / "broken.pdf"
    broken.write_bytes(b"%PDF-1.4 not really")
    report = run_batch(plan_batch([broken, good], merge=Into.PDF), overwrite=YES)
    by_name = {o.item.source.name: o for o in report.outcomes}
    assert by_name["good.pdf"].error is ErrorCode.NOTHING_TO_MERGE
    assert by_name["broken.pdf"].status is OutcomeStatus.FAILED
    assert report.unwritten_summaries == ()
    assert (workdir / "ClearMD_Output" / "Resumen_ClearMD.md").is_file()


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_03_the_texts_no_longer_guess_a_full_disk(language: str) -> None:
    catalog = load_catalog(language)
    for key in ("cli.summary_not_written", "gui.result.no_summary"):
        text = catalog.text_template(key).lower()
        assert "disk" not in text and "disco" not in text


def test_ac_04_merge_asks_for_two_documents_first() -> None:
    catalog = load_catalog("en")
    one = primary_of(catalog, 1, AppState.READY, [Path("/d/a.md")], None, None, Tool.MERGE)
    assert not one.enabled and one.hint == catalog.text("gui.nav.merge_needs_two")
    two = [Path("/d/a.md"), Path("/d/b.md")]
    assert primary_of(catalog, 1, AppState.READY, two, None, None, Tool.MERGE).enabled
    convert = primary_of(catalog, 1, AppState.READY, [Path("/d/a.md")], None, None)
    assert convert.enabled


def test_ac_04_merge_says_when_only_one_document_is_left(workdir: Path) -> None:
    (workdir / "a.md").write_text("a\n", "utf-8")
    (workdir / "b.docx").write_bytes(b"not a document")
    plan = plan_batch([workdir / "a.md", workdir / "c.xyz"], merge=Into.MARKDOWN)
    catalog = load_catalog("en")
    primary = primary_of(catalog, 2, AppState.WAITING_DECISION, [], plan, None, Tool.MERGE)
    assert len(plan.conversions) == 1
    assert not primary.enabled and primary.hint == catalog.text("gui.nav.merge_one_left")


@pytest.mark.parametrize("tool", ["convert", "split", "merge"])
def test_ac_05_a_folder_and_a_file_inside_it_give_the_file_once(workdir: Path, tool: str) -> None:
    folder = workdir / "docs"
    folder.mkdir()
    for name in ("a.txt", "b.txt"):
        (folder / name).write_text(f"{name}\n" * 20, "utf-8")
    options = {
        "convert": {},
        "split": {"split": SplitSpec(Cut.PARTS, 2, Keep.MARKDOWN)},
        "merge": {"merge": Into.MARKDOWN},
    }[tool]
    plan = plan_batch([folder, folder / "a.txt"], **options)  # type: ignore[arg-type]
    assert sorted(item.source.name for item in plan.conversions) == ["a.txt", "b.txt"]
    (repeat,) = [s for s in plan.skipped if s.reason is SkipReason.ALREADY_INCLUDED]
    assert repeat.path == folder / "a.txt"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("nombre;ciudad\nJosé;Bogotá\nAna;Cali\n", ";"),
        ("name\tcity\nJo\tParis\n", "\t"),
        ("a|b\n1|2\n", "|"),
        ("name,city\nJo,Paris\n", ","),
        ('name,note\nJo,"one; two; three"\n', ","),  # semicolons inside quotes: still commas
        ("just one column\nsecond\n", ","),
    ],
)
def test_ac_06_the_separator_is_found(text: str, expected: str) -> None:
    assert separator(text) == expected


def test_ac_06_a_semicolon_csv_keeps_its_columns(workdir: Path) -> None:
    source = workdir / "tabla.csv"
    source.write_bytes("﻿nombre;ciudad\nJosé;Bogotá\n".encode())
    run_batch(plan_batch([source]), overwrite=YES)
    text = (workdir / "ClearMD_Output" / "OutputMD" / "tabla.md").read_text("utf-8")
    assert "| nombre | ciudad |" in text and "| José | Bogotá |" in text


def _broken_links(markdown: Path) -> list[str]:
    import re

    links = re.findall(r"\]\(([^)\s]+)\)", markdown.read_text("utf-8"))
    local = [link for link in links if "://" not in link]
    return [link for link in local if not (markdown.parent / link).is_file()]


def test_ac_07_split_and_merge_keep_the_images(workdir: Path) -> None:
    (workdir / "doc_imagenes").mkdir()
    (workdir / "doc_imagenes" / "image-001.png").write_bytes(b"\x89PNG")
    body = "\n\n".join(f"# Part {n}\n\n![a chart](doc_imagenes/image-001.png)" for n in (1, 2))
    (workdir / "doc.md").write_text(body + "\n", "utf-8")
    (workdir / "other.md").write_text("[web](https://example.org) and [gone](missing.png)\n")
    run_batch(plan_batch([workdir / "doc.md"], split=SplitSpec(Cut.PARTS, 2)), overwrite=YES)
    parts = sorted((workdir / "ClearMD_Output" / "OutputSep" / "doc").glob("*.md"))
    assert len(parts) == 2 and all(not _broken_links(part) for part in parts)
    plan = plan_batch([workdir / "doc.md", workdir / "other.md"], merge=Into.MARKDOWN)
    run_batch(plan, overwrite=YES)
    (merged,) = (workdir / "ClearMD_Output" / "OutputUnif").iterdir()
    assert _broken_links(merged) == ["missing.png"]  # already broken: left as it was
    assert "(https://example.org)" in merged.read_text("utf-8")
    assert os.path.isfile(workdir / "doc_imagenes" / "image-001.png")


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_08_texts(language: str) -> None:
    catalog = load_catalog(language)
    for key in ("gui.nav.merge_needs_two", "gui.nav.merge_one_left", "skip.already_included"):
        assert catalog.text(key)
    assert catalog.text("merge.heading", index=2, total=3, name="b.pdf").endswith("b.pdf")
