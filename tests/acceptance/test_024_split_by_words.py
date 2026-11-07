"""Feature 024 — Split into parts that fit an AI, and Split takes Markdown
(spec/features/024_*/spec.md): the real worker, the parts read back."""

import shutil
from pathlib import Path

import pypdfium2 as pdfium
import pytest
from support import DOCUMENTS_DIR
from support.pdf_builder import Text, build_pdf

from clearmd.backend.api import Cut, Keep, SplitSpec, plan_batch, run_batch
from clearmd.backend.schemas.errors import ErrorCode, SkipReason
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.split.markdown_cut import cut_markdown
from clearmd.backend.services.split.words import count_words
from clearmd.backend.use_cases.splitting import word_ranges
from clearmd.frontend.cli import main
from clearmd.i18n import load_catalog

DOC = """# One

alpha beta gamma

```python
# not a heading
x = 1
```

## Two

delta epsilon

zeta eta theta iota

# Three

kappa
"""


def pdf(folder: Path, words_per_page: list[int], name: str = "book.pdf") -> Path:
    """A PDF whose pages hold that many words (in lines of ten)."""
    pages = []
    for count in words_per_page:
        lines = [" ".join(["word"] * min(10, count - start)) for start in range(0, count, 10)]
        pages.append([Text(line, 740 - 12 * row, size=8) for row, line in enumerate(lines)])
    path = folder / name
    path.write_bytes(build_pdf(pages))
    return path


def pages_in(path: Path) -> int:
    document = pdfium.PdfDocument(path.read_bytes())
    try:
        return len(document)
    finally:
        document.close()


def parts_of(workdir: Path, name: str) -> list[Path]:
    return sorted((workdir / "ClearMD_Output" / "OutputSep" / name).iterdir())


def test_ac_01_words_are_counted_with_cjk_characters_one_by_one() -> None:
    assert count_words("Hello, world: 2 cafés.") == 4
    assert count_words("日本語のテキスト") == 8


def test_ac_01_pages_are_grouped_whole_up_to_the_size_and_a_large_page_is_alone() -> None:
    ranges, over = word_ranges((300, 300, 300, 900, 100), 600)
    assert ranges == ((1, 2), (3, 3), (4, 4), (5, 5))
    assert over == (3,)


def test_ac_01_a_pdf_is_split_into_parts_of_about_n_words(workdir: Path) -> None:
    source = pdf(workdir, [300, 300, 300, 300, 300])
    plan = plan_batch([source], split=SplitSpec(Cut.WORDS, 600, Keep.PDF))
    report = run_batch(plan, overwrite=lambda item: True)
    assert [outcome.parts for outcome in report.outcomes] == [3]
    assert [pages_in(path) for path in parts_of(workdir, "book")] == [2, 2, 1]


def test_ac_01_a_page_over_the_size_is_a_part_alone_and_noted(workdir: Path) -> None:
    source = pdf(workdir, [100, 800, 100])
    plan = plan_batch([source], split=SplitSpec(Cut.WORDS, 500, Keep.PDF))
    outcome = run_batch(plan, overwrite=lambda item: True).outcomes[0]
    assert outcome.parts == 3
    assert [note.kind for note in outcome.notes] == [NoteKind.PARTS_OVER_SIZE]


def test_ac_01_a_pdf_without_text_fails_with_what_to_do(workdir: Path) -> None:
    source = workdir / "scan.pdf"
    source.write_bytes(build_pdf([[], []]))
    plan = plan_batch([source], split=SplitSpec(Cut.WORDS, 500))
    outcome = run_batch(plan, overwrite=lambda item: True).outcomes[0]
    assert outcome.error is ErrorCode.NOTHING_TO_MEASURE
    action = load_catalog("en").text(ErrorCode.NOTHING_TO_MEASURE.action_key)
    assert "every N pages" in action


def test_ac_02_markdown_is_cut_at_headings_and_never_inside_a_fence() -> None:
    parts, over = cut_markdown(DOC, Cut.PARTS, 3)
    assert "".join(parts) == DOC  # nothing inside changes
    assert [part.splitlines()[0] for part in parts] == ["# One", "## Two", "# Three"]
    assert "# not a heading" in parts[0] and over == ()


def test_ac_02_a_section_over_the_size_is_cut_at_paragraphs() -> None:
    parts, _ = cut_markdown(DOC, Cut.WORDS, 4)
    assert "".join(parts) == DOC
    assert any(part.startswith("zeta") for part in parts)  # "## Two" cut at its paragraphs
    plain = "one two three\n\nfour five six\n\nseven\n"
    parts, over = cut_markdown(plain, Cut.WORDS, 3)
    assert parts == ("one two three\n\n", "four five six\n\n", "seven\n") and over == ()


def test_ac_02_markdown_files_are_split_into_markdown_parts(workdir: Path) -> None:
    (workdir / "notes.md").write_text(DOC, "utf-8")
    plan = plan_batch([workdir / "notes.md"], split=SplitSpec(Cut.PARTS, 2, Keep.PDF))
    outcome = run_batch(plan, overwrite=lambda item: True).outcomes[0]
    assert outcome.parts == 2
    parts = parts_of(workdir, "notes")
    assert [path.suffix for path in parts] == [".md", ".md"]  # Markdown, whatever Keep says
    assert "".join(path.read_text("utf-8") for path in parts) == DOC


def test_ac_03_every_n_pages_leaves_markdown_out_with_a_reason(workdir: Path) -> None:
    (workdir / "notes.md").write_text(DOC, "utf-8")
    shutil.copyfile(DOCUMENTS_DIR / "sample.docx", workdir / "letter.docx")
    plan = plan_batch(
        [workdir / "notes.md", workdir / "letter.docx"], split=SplitSpec(Cut.PAGES, 2)
    )
    reasons = {item.path.name: item.reason for item in plan.skipped}
    assert reasons == {
        "notes.md": SkipReason.CUT_NOT_FOR_MARKDOWN,
        "letter.docx": SkipReason.NOT_SPLITTABLE,
    }


def test_ac_03_convert_still_leaves_markdown_out(workdir: Path) -> None:
    (workdir / "notes.md").write_text(DOC, "utf-8")
    plan = plan_batch([workdir / "notes.md"])
    assert [item.reason for item in plan.skipped] == [SkipReason.ALREADY_MARKDOWN]


def test_ac_04_the_command_line_splits_by_words(workdir: Path) -> None:
    source = pdf(workdir, [400, 400, 400])
    assert main([str(source), "--quiet", "--split-words", "500", "--keep", "pdf"]) == 0
    assert len(parts_of(workdir, "book")) == 3


@pytest.mark.parametrize(
    "arguments",
    [["--split-words", "499"], ["--split-words", "600", "--split-parts", "2"]],
)
def test_ac_04_wrong_word_arguments_are_refused(workdir: Path, arguments: list[str]) -> None:
    source = pdf(workdir, [10])
    with pytest.raises(SystemExit) as stop:
        main([str(source), *arguments])
    assert stop.value.code == 2


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_06_the_size_is_always_about_and_no_ai_is_named(language: str) -> None:
    catalog = load_catalog(language)
    about = {"en": "about", "es": "unas"}[language]
    for key in ("gui.split.by_words", "gui.settings.split_words", "cli.help.split_words"):
        assert about in catalog.text_template(key).lower()
    assert about in catalog.text("gui.split.words")
    every = " ".join(catalog.text_template(key) for key in catalog.keys())
    for brand in ("ChatGPT", "Claude", "Gemini", "GPT-", "Copilot"):
        assert brand not in every
