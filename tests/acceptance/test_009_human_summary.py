"""Feature 009 — one test per acceptance criterion (spec/features/009_*/spec.md): real batches
through the command line, the summary read back; the choice on the window."""

import shutil
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import pypdfium2 as pdfium
import pytest
from markdown_it import MarkdownIt
from support import DOCUMENTS_DIR
from support.gui_close import shut
from support.gui_fakes import FakeBackend

from clearmd.backend.api import composition
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.cli import main
from clearmd.frontend.ttk import TtkApp

ROOT = Path(__file__).resolve().parents[2]


def put(workdir: Path, fixture: str, name: str) -> Path:
    """Into the batch's folder, ``docs`` (its results go next to it, in workdir)."""
    folder = workdir / "docs" / Path(name).parent
    name = Path(name).name
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / name
    shutil.copyfile(DOCUMENTS_DIR / fixture, target)
    return target


def summary(folder: Path) -> str:
    return (folder / "ClearMD_Output" / "Resumen_ClearMD.md").read_text(encoding="utf-8")


def pdf_text(folder: Path) -> str:
    document = pdfium.PdfDocument(str(folder / "ClearMD_Output" / "Resumen_ClearMD.pdf"))
    try:
        return "\n".join(page.get_textpage().get_text_range() for page in document)
    finally:
        document.close()


def mixed(workdir: Path) -> None:
    put(workdir, "sample.txt", "notes.txt")
    put(workdir, "sample.docx", "thesis/chapter.docx")
    put(workdir, "corrupt.docx", "broken.docx")
    put(workdir, "sample.txt", "old.md")


def test_ac_01_a_headline_first_then_the_batch_line(workdir: Path) -> None:
    put(workdir, "sample.txt", "a.txt")
    put(workdir, "sample.txt", "b.txt")
    assert main([str(workdir / "docs"), "--quiet"]) == 0
    lines = summary(workdir).splitlines()
    assert lines[2] == "✅ **All 2 documents were converted.**"
    assert " · ClearMD " in lines[4] and lines[4].endswith("2 converted · 0 skipped · 0 failed")


def test_ac_01_with_problems_the_mark_and_the_count_say_so(workdir: Path) -> None:
    mixed(workdir)
    main([str(workdir / "docs"), "--quiet"])
    assert summary(workdir).splitlines()[2] == (
        "⚠️ **2 of 3 documents were converted.** One thing needs your attention."
    )


def test_ac_02_where_the_files_are(workdir: Path) -> None:
    mixed(workdir)
    main([str(workdir / "docs"), "--quiet"])
    text = summary(workdir)
    assert "## Where your files are\nYour Markdown files are in the `OutputMD/` folder" in text


def test_ac_03_what_needs_attention_comes_before_the_rest(workdir: Path) -> None:
    mixed(workdir)
    main([str(workdir / "docs"), "--quiet"])
    text = summary(workdir)
    attention = text.index("## Needs your attention")
    assert attention < text.index("## Converted") < text.index("## Left out")
    assert "- ❌ `broken.docx` in `docs` — This file seems to be damaged. " in text


def test_ac_04_names_with_their_folder_apart_in_a_table(workdir: Path) -> None:
    mixed(workdir)
    main([str(workdir / "docs"), "--quiet"])
    text = summary(workdir)
    assert "| `chapter.docx` | `docs/thesis` | `docs/thesis/chapter.md` | DOCX |" in text
    assert "| `notes.txt` | `docs` | `docs/notes.md` | TXT |" in text
    assert str(workdir) not in text  # never a long absolute path


def test_ac_05_the_history_is_folded_and_kept(workdir: Path) -> None:
    put(workdir, "sample.txt", "a.txt")
    main([str(workdir / "docs"), "--quiet"])
    first = summary(workdir).splitlines()[4]
    main([str(workdir / "docs"), "--quiet", "--overwrite"])
    text = summary(workdir)
    folded = text.split("<details>\n<summary>History</summary>", 1)[1]
    assert f"- {first}" in folded and folded.rstrip().endswith("</details>")


def test_ac_06_a_hostile_name_never_breaks_the_summary(workdir: Path) -> None:
    for name in ("a|b `c`.txt", "# heading.txt", "[x](javascript:alert(1)).txt", "<img src=x>.txt"):
        put(workdir, "sample.txt", name)
    main([str(workdir / "docs"), "--quiet"])
    tokens = MarkdownIt("commonmark", {"html": True}).enable("table").parse(summary(workdir))
    html = [t.content for t in tokens if t.type in {"html_block", "html_inline"}]
    assert all(block.startswith(("<details", "</details", "<summary", "<!--")) for block in html)
    assert not any(t.type == "link_open" for t in tokens for t in (t.children or []))
    headings = [t for t in tokens if t.type == "heading_open"]
    assert all(t.markup in {"#", "##"} for t in headings)


def test_ac_07_spanish_singular_and_plural(workdir: Path) -> None:
    put(workdir, "sample.txt", "a.txt")
    main([str(workdir / "docs"), "--quiet", "--lang", "es"])
    assert summary(workdir).splitlines()[2] == "✅ **El documento se convirtió.**"
    put(workdir, "corrupt.docx", "roto.docx")
    main([str(workdir / "docs"), "--quiet", "--lang", "es", "--overwrite"])
    assert "Una cosa necesita tu atención." in summary(workdir).splitlines()[2]


def test_ac_08_the_pdf_report_next_to_the_markdown(workdir: Path) -> None:
    mixed(workdir)
    main([str(workdir / "docs"), "--quiet", "--summary-pdf"])
    text = pdf_text(workdir)
    assert "2 of 3 documents were converted. One thing needs your attention." in text
    assert (
        "Where your files are" in text
        and "broken.docx in docs — This file seems to be damaged." in text
    )
    assert "chapter.docx docs/thesis docs/thesis/chapter.md DOCX" in text
    data = (workdir / "ClearMD_Output" / "Resumen_ClearMD.pdf").read_bytes()
    assert b"/URI" not in data and b"/JavaScript" not in data and b"/OpenAction" not in data


def test_ac_09_a_pdf_that_cannot_be_written_leaves_the_markdown_and_is_told(
    workdir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class Broken:
        def write(self, report: object) -> None:
            raise OSError("disk full")

    monkeypatch.setattr(composition, "build_pdf_report", lambda language: Broken())
    put(workdir, "sample.txt", "a.txt")
    assert main([str(workdir / "docs"), "--summary-pdf"]) == 0
    assert summary(workdir).startswith("# ClearMD summary")
    assert "The PDF summary in" in capsys.readouterr().err


@pytest.fixture
def app(display: str) -> Iterator[TtkApp]:
    window = TtkApp(FakeBackend(settings=Settings(show_welcome=False)))
    window.start()
    yield window
    shut(window)


def pump(app: TtkApp, until: Callable[[], bool], seconds: float = 3.0) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline and not until():
        app.root.update()
        time.sleep(0.01)


def test_ac_10_the_format_on_step_1_remembered_in_settings_and_the_cli(app: TtkApp) -> None:
    pdf = app.main.summary_buttons[1]
    assert app.main.summary_format.get() == "markdown"
    pdf.invoke()
    assert app.presenter.settings.summary_format == "markdown_pdf"
    fake = app.presenter._backend
    assert isinstance(fake, FakeBackend) and fake.settings.summary_format == "markdown_pdf"
    app.show_settings()
    pump(app, lambda: app.dialog is not None)
    assert app.dialog is not None and "summary_format" in getattr(app.dialog, "values", {})
    app.dialog.close()
    help_text = (ROOT / "src/clearmd/i18n/en.toml").read_text(encoding="utf-8")
    assert "summary_pdf = " in help_text


def test_ac_11_samples_of_the_summary_and_screenshots_of_the_choice() -> None:
    shots = ROOT / "docs" / "screenshots" / "009"
    for language in ("en", "es"):
        for name in (f"summary-{language}.md", f"summary-{language}.pdf",
                     f"summary-pdf-{language}.png"):  # fmt: skip
            assert (shots / name).is_file(), name
        for theme in ("light", "dark"):
            for screen in ("1-choose", "6-settings"):
                assert (shots / f"{screen}-{theme}-{language}.png").is_file(), screen
