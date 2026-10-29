"""Resumen_ClearMD.md: content per language, history and escaping (AC-28, AC-29, AC-41)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from clearmd.backend.schemas.errors import ErrorCode, SkipReason
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import (
    ConversionOutcome,
    Detection,
    DetectionMethod,
    OutcomeStatus,
    OutputRootReport,
    PlannedConversion,
    SkippedItem,
)
from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind
from clearmd.backend.services.summary.writer import HISTORY_LIMIT, MarkdownSummaryWriter
from clearmd.i18n import load_catalog

BOGOTA = timezone(timedelta(hours=-5))
NOW = datetime(2026, 10, 25, 15, 30, tzinfo=BOGOTA)


def _item(
    parent: Path,
    source: str,
    target: str,
    fmt: FormatId,
    *,
    by_content: bool = False,
    cost: float = 1,
) -> PlannedConversion:
    root = parent / "ClearMD_Output"
    method = DetectionMethod.CONTENT if by_content else DetectionMethod.EXTENSION
    return PlannedConversion(
        source=parent / source,
        output_root=root,
        target=root / "OutputMD" / target,
        detection=Detection(fmt, method),
        exists=False,
        cost=cost,
    )


def _report(parent: Path, *, started_at: datetime = NOW) -> OutputRootReport:
    root = parent / "ClearMD_Output"
    pdf = FormatId.PDF
    return OutputRootReport(
        root=root,
        started_at=started_at,
        finished_at=started_at + timedelta(seconds=40),
        outcomes=(
            ConversionOutcome(
                _item(parent, "project/notes.pdf", "project/notes.md", pdf),
                OutcomeStatus.CONVERTED,
                seconds=28.4,
            ),
            ConversionOutcome(
                _item(parent, "project/scan", "project/scan.md", FormatId.DOCX, by_content=True),
                OutcomeStatus.CONVERTED,
                seconds=0.4,
            ),
            ConversionOutcome(
                _item(parent, "project/manual.pdf", "project/manual.md", pdf, cost=900),
                OutcomeStatus.STOPPED,
                ErrorCode.TIMED_OUT,
                "stopped after 600 s",
                seconds=600,
                limit=600,
            ),
            ConversionOutcome(
                _item(parent, "project/contract.pdf", "project/contract.md", pdf),
                OutcomeStatus.FAILED,
                ErrorCode.PASSWORD_PROTECTED,
                "PDFPasswordIncorrect",
                seconds=0.2,
            ),
        ),
        skipped=(
            SkippedItem(parent / "project" / ".cache", SkipReason.HIDDEN, is_dir=True),
            SkippedItem(parent / "project" / "old.md", SkipReason.ALREADY_MARKDOWN),
        ),
        cancelled=False,
    )


EXPECTED_EN = "\n".join(
    [
        "# ClearMD summary",
        "",
        "⚠️ **2 of 4 documents were converted.** 2 things need your attention.",
        "",
        "2026-10-25 15:30 · ClearMD 0.1.0 · 2 converted · 2 skipped · 1 failed · 1 stopped",
        "",
        "## Where your files are",
        "Your Markdown files are in the `OutputMD/` folder, next to this summary.",
        "",
        "## Needs your attention",
        "- ❌ `contract.pdf` in `project` — This file is password-protected. Remove the password and try again.",  # noqa: E501 (the summary as written)
        "  <details><summary>Technical detail</summary>PDFPasswordIncorrect</details>",
        "- ⏹️ `manual.pdf` in `project` — Exceeded the time limit (10 min). Estimated progress: 67% after 10:00. Try splitting it into smaller files.",  # noqa: E501 (the summary as written)
        "",
        "## Converted",
        "| Document | Folder | Result | Format | Time |",
        "|---|---|---|---|---|",
        "| `notes.pdf` | `project` | `notes.md` | PDF | 28 s |",
        "| `scan` | `project` | `scan.md` | DOCX, detected by content | <1 s |",
        "",
        "## Left out",
        "- `.cache/` in `project` — Hidden file. Make it visible to convert it.",
        "- `old.md` in `project` — Already Markdown. It needs no conversion.",
        "",
        "<details>",
        "<summary>History</summary>",
        "",
        "<!-- clearmd:history -->",
        "_No earlier batches here._",
        "<!-- /clearmd:history -->",
        "",
        "</details>",
        "",
    ]
)


def _write(tmp_path: Path, language: str = "en", **kwargs: datetime) -> str:
    writer = MarkdownSummaryWriter(load_catalog(language), version="0.1.0")
    report = _report(tmp_path, **kwargs)
    report.root.mkdir(exist_ok=True)
    writer.write(report)
    return (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")


def test_the_summary_in_english(tmp_path: Path) -> None:
    assert _write(tmp_path) == EXPECTED_EN


def test_the_summary_in_spanish(tmp_path: Path) -> None:
    text = _write(tmp_path, "es")
    assert text.startswith("# Resumen de ClearMD\n\n⚠️ **Se convirtieron 2 de 4 documentos.**")
    assert "\n2026-10-25 15:30 · ClearMD 0.1.0 · 2 convertidos" in text
    for heading in (
        "## Dónde están tus archivos",
        "## Necesita tu atención",
        "## Convertidos",
        "## No incluidos",
        "<summary>Historial</summary>",
    ):
        assert heading in text
    assert "| Documento | Carpeta | Resultado | Formato | Tiempo |" in text
    assert "DOCX, detectado por su contenido" in text
    assert "Este archivo está protegido con contraseña." in text


def test_the_previous_batch_moves_into_the_history(tmp_path: Path) -> None:
    _write(tmp_path, started_at=NOW - timedelta(days=1))
    _write(tmp_path, started_at=NOW - timedelta(hours=2))
    text = _write(tmp_path)
    history = text.split("<!-- clearmd:history -->\n", 1)[1].split("<!-- /clearmd:history -->", 1)[
        0
    ]
    assert history.splitlines() == [
        "- 2026-10-25 13:30 · ClearMD 0.1.0 · 2 converted · 2 skipped · 1 failed · 1 stopped",
        "- 2026-10-24 15:30 · ClearMD 0.1.0 · 2 converted · 2 skipped · 1 failed · 1 stopped",
    ]


def test_an_unreadable_previous_summary_restarts_the_history_and_says_so(tmp_path: Path) -> None:
    root = tmp_path / "ClearMD_Output"
    root.mkdir()
    (root / "Resumen_ClearMD.md").write_text("someone edited this by hand", encoding="utf-8")
    text = _write(tmp_path)
    assert "The previous history could not be read, so it starts again here." in text


def test_the_history_is_capped(tmp_path: Path) -> None:
    root = tmp_path / "ClearMD_Output"
    root.mkdir()
    lines = "\n".join(
        f"- 2026-01-01 10:{n % 60:02d} · ClearMD 0.1.0 · {n} converted · 0 skipped · 0 failed"
        for n in range(HISTORY_LIMIT + 50)
    )
    (root / "Resumen_ClearMD.md").write_text(
        f"# ClearMD summary\nheader\n\n<!-- clearmd:history -->\n## History\n{lines}\n"
        "<!-- /clearmd:history -->\n",
        encoding="utf-8",
    )
    text = _write(tmp_path)
    assert text.count("\n- 2026-01-01 10:") == HISTORY_LIMIT  # the malformed "header" is dropped


@pytest.mark.parametrize(
    ("name", "shown"),
    [
        ("a|b.pdf", "`a\\|b.pdf`"),
        ("tick`name.pdf", "`` tick`name.pdf ``"),
    ],
)
def test_untrusted_names_cannot_break_the_table(tmp_path: Path, name: str, shown: str) -> None:
    writer = MarkdownSummaryWriter(load_catalog("en"), version="0.1.0")
    outcome = ConversionOutcome(
        _item(tmp_path, name, "x.md", FormatId.PDF), OutcomeStatus.CONVERTED, seconds=1
    )
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, (outcome,), (), False)
    report.root.mkdir()
    writer.write(report)
    lines = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8").splitlines()
    row = lines[lines.index("|---|---|---|---|---|") + 1]
    assert row.startswith(f"| {shown} |") and row.count(" | ") == 4  # still five cells


def test_technical_details_cannot_inject_html(tmp_path: Path) -> None:
    writer = MarkdownSummaryWriter(load_catalog("en"), version="0.1.0")
    outcome = ConversionOutcome(
        _item(tmp_path, "x.pdf", "x.md", FormatId.PDF),
        OutcomeStatus.FAILED,
        ErrorCode.CONVERSION_FAILED,
        "ValueError: <script>alert(1)</script> & more",
    )
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, (outcome,), (), False)
    report.root.mkdir()
    writer.write(report)
    text = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    assert "<script>" not in text
    assert "&lt;script&gt;alert(1)&lt;/script&gt; &amp; more" in text


def test_kept_and_cancelled_items_have_their_sections(tmp_path: Path) -> None:
    writer = MarkdownSummaryWriter(load_catalog("en"), version="0.1.0")
    kept = ConversionOutcome(_item(tmp_path, "a.pdf", "a.md", FormatId.PDF), OutcomeStatus.KEPT)
    gone = ConversionOutcome(
        _item(tmp_path, "b.pdf", "b.md", FormatId.PDF), OutcomeStatus.CANCELLED
    )
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, (kept, gone), (), True)
    report.root.mkdir()
    writer.write(report)
    text = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    assert "## Kept (the output already existed)\n- `a.pdf` → `a.md`" in text
    assert "## Cancelled\n- ⏹️ `b.pdf`" in text
    assert text.splitlines()[4].endswith(" · cancelled")  # the batch line


def test_a_planted_summary_link_is_neither_read_nor_written_through(tmp_path: Path) -> None:
    victim = tmp_path / "victim.txt"
    victim.write_text("precious <!-- clearmd:history -->", encoding="utf-8")
    root = tmp_path / "ClearMD_Output"
    root.mkdir()
    (root / "Resumen_ClearMD.md").symlink_to(victim)
    text = _write(tmp_path)
    assert victim.read_text(encoding="utf-8") == "precious <!-- clearmd:history -->"
    assert "precious" not in text


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("a``b.pdf", "``` a``b.pdf ```"),
        ("evil\n- injected.pdf", "`evil\\x0a- injected.pdf`"),
        # A "/" makes it a folder and a name: both stay code spans.
        ("fake<!-- /clearmd:history -->.pdf", "`clearmd:history -->.pdf`"),
    ],
)
def test_names_cannot_escape_their_code_span_or_line(
    tmp_path: Path, name: str, expected: str
) -> None:
    writer = MarkdownSummaryWriter(load_catalog("en"), version="0.1.0")
    outcome = ConversionOutcome(
        _item(tmp_path, name, "x.md", FormatId.PDF),
        OutcomeStatus.FAILED,
        ErrorCode.CORRUPT_FILE,
        "x",
    )
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, (outcome,), (), False)
    report.root.mkdir()
    writer.write(report)
    text = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    assert f"- ❌ {expected} — " in text
    assert text.split("\n").count("<!-- /clearmd:history -->") == 1  # only ClearMD's own marker
    assert "\n- injected" not in text


def test_a_technical_detail_stays_on_one_line(tmp_path: Path) -> None:
    writer = MarkdownSummaryWriter(load_catalog("en"), version="0.1.0")
    outcome = ConversionOutcome(
        _item(tmp_path, "x.pdf", "x.md", FormatId.PDF),
        OutcomeStatus.FAILED,
        ErrorCode.CONVERSION_FAILED,
        "line one\n\n# Injected heading\nline two",
    )
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, (outcome,), (), False)
    report.root.mkdir()
    writer.write(report)
    text = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    assert "\n# Injected heading" not in text
    assert "line one # Injected heading line two" in text


def test_a_name_cannot_inject_history_lines_on_the_next_run(tmp_path: Path) -> None:
    name = "<!-- clearmd:history -->\u2028- <img src=x>.pdf"
    writer = MarkdownSummaryWriter(load_catalog("en"), version="0.1.0")
    outcome = ConversionOutcome(
        _item(tmp_path, name, "x.md", FormatId.PDF), OutcomeStatus.CONVERTED, seconds=1
    )
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, (outcome,), (), False)
    report.root.mkdir()
    writer.write(report)
    writer.write(report)  # the second run reads the first summary's history
    text = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    history = text.split("\n<!-- clearmd:history -->\n", 1)[1]
    assert "<img" not in history
    assert history.splitlines()[0].startswith("- 2026-10-25 15:30 · ClearMD 0.1.0 · ")


def test_only_well_formed_history_lines_are_carried_over(tmp_path: Path) -> None:
    root = tmp_path / "ClearMD_Output"
    root.mkdir()
    (root / "Resumen_ClearMD.md").write_text(
        "# ClearMD summary\n<script>header</script>\n\n<!-- clearmd:history -->\n## History\n"
        "- 2026-10-01 10:00 · ClearMD 0.1.0 · 3 converted · 0 skipped · 0 failed\n"
        "- [click me](http://example.com)\n"
        "<!-- /clearmd:history -->\n",
        encoding="utf-8",
    )
    text = _write(tmp_path)
    history = text.split("\n<!-- clearmd:history -->\n", 1)[1]
    assert "- 2026-10-01 10:00 · ClearMD 0.1.0 · 3 converted · 0 skipped · 0 failed" in history
    assert "click me" not in history and "<script>" not in history


def test_an_oversized_previous_summary_is_not_read(tmp_path: Path) -> None:
    root = tmp_path / "ClearMD_Output"
    root.mkdir()
    with (root / "Resumen_ClearMD.md").open("wb") as handle:
        handle.truncate(100 * 1024**2)  # sparse: no real disk space
    text = _write(tmp_path)
    assert "The previous history could not be read" in text


def _noted_report(tmp_path: Path, notes: tuple[ConversionNote, ...]) -> OutputRootReport:
    outcome = ConversionOutcome(
        _item(tmp_path, "thesis/main.tex", "thesis/main.md", FormatId.PDF),
        OutcomeStatus.CONVERTED,
        seconds=2,
        notes=notes,
    )
    root = tmp_path / "ClearMD_Output"
    root.mkdir(exist_ok=True)
    return OutputRootReport(root, NOW, NOW, (outcome,), (), False)


@pytest.mark.parametrize(
    ("language", "heading", "unknown", "include"),
    [
        (
            "en",
            "## Needs your attention",
            "commands ClearMD does not know were left as written: `\\foo`, `\\bar`",
            "includes not followed: `../secret.tex` (outside the document folder)",
        ),
        (
            "es",
            "## Necesita tu atención",
            "se dejaron tal cual comandos que ClearMD no conoce: `\\foo`, `\\bar`",
            "no se siguieron estas inclusiones: `../secret.tex`"
            " (fuera de la carpeta del documento)",
        ),
    ],
)
def test_notes_are_listed_in_the_users_language(
    tmp_path: Path, language: str, heading: str, unknown: str, include: str
) -> None:
    notes = (
        ConversionNote(NoteKind.UNKNOWN_COMMANDS, (NoteItem("\\foo"), NoteItem("\\bar"))),
        ConversionNote(
            NoteKind.INCLUDE_NOT_FOLLOWED, (NoteItem("../secret.tex", "outside_folder"),)
        ),
    )
    writer = MarkdownSummaryWriter(load_catalog(language), version="0.1.0")
    report = _noted_report(tmp_path, notes)
    writer.write(report)
    text = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    section = text.split(heading + "\n", 1)[1].split("\n\n", 1)[0]
    first = {"en": "- ⚠️ `main.tex` in `thesis` — converted, but:",
             "es": "- ⚠️ `main.tex` en `thesis` — se convirtió, pero:"}[language]  # fmt: skip
    assert section.splitlines() == [first, f"  - {unknown}", f"  - {include}"]


def test_a_long_list_of_names_is_cut_at_twenty(tmp_path: Path) -> None:
    items = tuple(NoteItem(f"\\cmd{chr(97 + n)}") for n in range(25))
    writer = MarkdownSummaryWriter(load_catalog("en"), version="0.1.0")
    report = _noted_report(tmp_path, (ConversionNote(NoteKind.UNKNOWN_COMMANDS, items),))
    writer.write(report)
    text = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    assert "`\\cmdt` and 5 more" in text
    assert "`\\cmdu`" not in text


def test_files_without_notes_have_no_notes_section(tmp_path: Path) -> None:
    assert "converted, but" not in _write(tmp_path)


# --- Code review of 009 (C9-*) -------------------------------------------------------------------


def test_c9_1_nothing_tried_and_something_left_out_is_no_success(tmp_path: Path) -> None:
    kept = ConversionOutcome(_item(tmp_path, "a.pdf", "a.md", FormatId.PDF), OutcomeStatus.KEPT)
    left = SkippedItem(tmp_path / "b.xyz", SkipReason.UNSUPPORTED_FORMAT)
    writer = MarkdownSummaryWriter(load_catalog("en"), version="0.1.0")
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, (kept,), (left,), False)
    report.root.mkdir()
    writer.write(report)
    text = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    assert text.splitlines()[2] == "⚠️ **Nothing was converted: see what was left out.**"


def test_c9_2_the_folder_is_the_results_never_an_absolute_path(tmp_path: Path) -> None:
    chosen = tmp_path / "elsewhere" / "ClearMD_Output"
    item = PlannedConversion(
        source=tmp_path / "Documents" / "top.txt",
        output_root=chosen,
        target=chosen / "OutputMD" / "Documents" / "top.md",
        detection=Detection(FormatId.TXT, DetectionMethod.EXTENSION),
        exists=False,
        cost=1,
    )
    report = OutputRootReport(
        chosen, NOW, NOW, (ConversionOutcome(item, OutcomeStatus.CONVERTED),), (), False
    )
    chosen.mkdir(parents=True)
    MarkdownSummaryWriter(load_catalog("en"), version="0.1.0").write(report)
    text = (chosen / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    assert "| `top.txt` | `Documents` | `top.md` |" in text and str(tmp_path) not in text


@pytest.mark.parametrize(
    ("language", "counts", "headline"),
    [
        ("es", (1, 2), "⚠️ **Se convirtió 1 de 3 documentos.**"),
        ("en", (1, 2), "⚠️ **1 of 3 documents was converted.**"),
        ("es", (2, 1), "⚠️ **Se convirtieron 2 de 3 documentos.**"),
    ],
)
def test_c9_7_singular_and_plural(
    tmp_path: Path, language: str, counts: tuple[int, int], headline: str
) -> None:
    converted, failed = counts
    outcomes = tuple(
        ConversionOutcome(_item(tmp_path, f"c{n}.pdf", f"c{n}.md", FormatId.PDF),
                          OutcomeStatus.CONVERTED)
        for n in range(converted)
    ) + tuple(
        ConversionOutcome(_item(tmp_path, f"f{n}.pdf", f"f{n}.md", FormatId.PDF),
                          OutcomeStatus.FAILED, ErrorCode.CORRUPT_FILE)
        for n in range(failed)
    )  # fmt: skip
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, outcomes, (), False)
    report.root.mkdir()
    MarkdownSummaryWriter(load_catalog(language), version="0.1.0").write(report)
    lines = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8").splitlines()
    assert lines[2].startswith(headline)
    if language == "es" and converted == 1:
        assert "1 convertido · 0 omitidos · 2 con error" in lines[4]


# --- Adversarial check of 009 (A9-*) ---------------------------------------------------------


def test_a9_1_a_batch_of_thousands_stays_in_the_history(tmp_path: Path) -> None:
    outcomes = tuple(
        ConversionOutcome(_item(tmp_path, f"d{n}.txt", f"d{n}.md", FormatId.TXT),
                          OutcomeStatus.CONVERTED)
        for n in range(1500)
    )  # fmt: skip
    report = OutputRootReport(tmp_path / "ClearMD_Output", NOW, NOW, outcomes, (), False)
    report.root.mkdir()
    writer = MarkdownSummaryWriter(load_catalog("es"), version="0.1.0")
    writer.write(report)
    writer.write(report)
    text = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    history = text.split("<!-- clearmd:history -->\n", 1)[1]
    assert history.startswith("- 2026-10-25 15:30 · ClearMD 0.1.0 · 1.500 convertidos · ")
