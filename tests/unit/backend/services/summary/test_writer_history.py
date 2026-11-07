"""Resumen_ClearMD.md: the history of previous batches (AC-29)."""

from datetime import timedelta
from pathlib import Path

from support.summary_cases import NOW, _item, _write

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import (
    ConversionOutcome,
    OutcomeStatus,
    OutputRootReport,
)
from clearmd.backend.services.summary.writer import HISTORY_LIMIT, MarkdownSummaryWriter
from clearmd.i18n import load_catalog


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
        f"# ClearMD Summary\nheader\n\n<!-- clearmd:history -->\n## History\n{lines}\n"
        "<!-- /clearmd:history -->\n",
        encoding="utf-8",
    )
    text = _write(tmp_path)
    assert text.count("\n- 2026-01-01 10:") == HISTORY_LIMIT  # the malformed "header" is dropped


def test_a_planted_summary_link_is_neither_read_nor_written_through(tmp_path: Path) -> None:
    victim = tmp_path / "victim.txt"
    victim.write_text("precious <!-- clearmd:history -->", encoding="utf-8")
    root = tmp_path / "ClearMD_Output"
    root.mkdir()
    (root / "Resumen_ClearMD.md").symlink_to(victim)
    text = _write(tmp_path)
    assert victim.read_text(encoding="utf-8") == "precious <!-- clearmd:history -->"
    assert "precious" not in text


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
        "# ClearMD Summary\n<script>header</script>\n\n<!-- clearmd:history -->\n## History\n"
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
