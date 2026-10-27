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
        "2026-10-25 15:30 · ClearMD 0.1.0 · 2 converted · 2 skipped · 1 failed · 1 stopped",
        "",
        "## Converted",
        "| Source | Output | Format | Time |",
        "|---|---|---|---|",
        "| `project/notes.pdf` | `OutputMD/project/notes.md` | PDF | 28 s |",
        "| `project/scan` | `OutputMD/project/scan.md` | DOCX, detected by content | <1 s |",
        "",
        "## Stopped",
        "- `project/manual.pdf` — Exceeded the time limit (10 min). Estimated progress: 67% after"
        " 10:00. Try splitting it into smaller files.",
        "",
        "## Failed",
        "- `project/contract.pdf` — This file is password-protected."
        " Remove the password and try again.",
        "  <details><summary>Technical detail</summary>PDFPasswordIncorrect</details>",
        "",
        "## Skipped",
        "- `project/.cache/` — hidden file. Make it visible to convert it.",
        "- `project/old.md` — already Markdown. It needs no conversion.",
        "",
        "<!-- clearmd:history -->",
        "## History",
        "<!-- /clearmd:history -->",
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
    assert text.startswith("# Resumen de ClearMD\n2026-10-25 15:30 · ClearMD 0.1.0 · 2 convertidos")
    for heading in (
        "## Convertidos",
        "## Detenidos",
        "## Con error",
        "## Omitidos",
        "## Historial",
    ):
        assert heading in text
    assert "| Origen | Resultado | Formato | Tiempo |" in text
    assert "DOCX, detectado por su contenido" in text
    assert "Este archivo está protegido con contraseña." in text


def test_the_previous_batch_moves_into_the_history(tmp_path: Path) -> None:
    _write(tmp_path, started_at=NOW - timedelta(days=1))
    _write(tmp_path, started_at=NOW - timedelta(hours=2))
    text = _write(tmp_path)
    history = text.split("## History\n", 1)[1].split("<!-- /clearmd:history -->", 1)[0]
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
    row = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8").splitlines()[6]
    assert row.startswith(f"| {shown} |")


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
    assert "## Kept (the output already existed)\n- `a.pdf` → `OutputMD/a.md`" in text
    assert "## Cancelled\n- `b.pdf`" in text
    assert "cancelled" in text.splitlines()[1]


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
        ("fake<!-- /clearmd:history -->.pdf", "`fake<!-- /clearmd:history -->.pdf`"),
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
    assert f"- {expected} — " in text
    assert text.count("<!-- /clearmd:history -->") == 2 if "history" in name else True
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
    history = text.split("\n## History\n", 1)[1]
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
    history = text.split("\n## History\n", 1)[1]
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
            "## Converted with notes",
            "commands ClearMD does not know were left as written: `\\foo`, `\\bar`",
            "includes not followed: `../secret.tex` (outside the document folder)",
        ),
        (
            "es",
            "## Convertidos con notas",
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
    assert section.splitlines() == ["- `thesis/main.tex`", f"  - {unknown}", f"  - {include}"]


def test_a_long_list_of_names_is_cut_at_twenty(tmp_path: Path) -> None:
    items = tuple(NoteItem(f"\\cmd{chr(97 + n)}") for n in range(25))
    writer = MarkdownSummaryWriter(load_catalog("en"), version="0.1.0")
    report = _noted_report(tmp_path, (ConversionNote(NoteKind.UNKNOWN_COMMANDS, items),))
    writer.write(report)
    text = (report.root / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    assert "`\\cmdt` and 5 more" in text
    assert "`\\cmdu`" not in text


def test_files_without_notes_have_no_notes_section(tmp_path: Path) -> None:
    assert "with notes" not in _write(tmp_path)
