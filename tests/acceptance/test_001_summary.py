"""Feature 001 — the summary written in each output root (spec/features/001_*/spec.md)."""

from pathlib import Path

import pytest
from support import put
from support.batch_cli import _summary

from clearmd.frontend.cli import main


def test_ac_22_and_ac_28_each_output_root_gets_its_summary(workdir: Path) -> None:
    good = put(workdir / "one", "sample.txt", "notes.txt")
    broken = put(workdir / "one", "corrupt.docx", "broken.docx")
    scan = put(workdir / "one", "docx_without_extension", "scan")
    other = put(workdir / "two", "sample.txt", "other.txt")
    (workdir / "one" / "old.md").write_text("# hi", encoding="utf-8")
    arguments = [str(good), str(broken), str(scan), str(other), str(workdir / "one" / "old.md")]
    assert main([*arguments, "--quiet"]) == 1
    one = _summary(workdir / "one")
    assert "| `notes.txt` | — | `notes.md` | TXT |" in one
    assert "| `scan` | — | `scan.md` | DOCX, detected by content |" in one
    assert "- ❌ `broken.docx` — This file seems to be damaged." in one
    assert "<details><summary>Technical Detail</summary>BadZipFile" in one
    assert "- `old.md` — Already Markdown" in one
    assert "other.txt" not in one
    assert "`other.txt`" in _summary(workdir / "two")


def test_ac_29_the_history_keeps_earlier_batches(workdir: Path) -> None:
    source = put(workdir, "sample.txt", "notes.txt")
    assert main([str(source), "--quiet"]) == 0
    first_header = _summary(workdir).splitlines()[4]  # the batch line, under the headline
    assert main([str(source), "--overwrite", "--quiet"]) == 0
    history = _summary(workdir).split("<!-- clearmd:history -->", 1)[1]
    assert f"- {first_header}" in history


def test_ac_41_the_summary_shows_the_time_of_each_file(workdir: Path) -> None:
    source = put(workdir, "sample.pdf", "report.pdf")
    assert main([str(source), "--quiet"]) == 0
    row = next(line for line in _summary(workdir).splitlines() if "`report.pdf`" in line)
    assert row.endswith(" s |")  # "<1 s" or "N s"


def test_ac_28_the_summary_speaks_spanish_when_asked(workdir: Path) -> None:
    from clearmd.backend.api import plan_batch, run_batch

    source = put(workdir, "sample.txt", "notas.txt")
    plan = plan_batch([source])
    run_batch(plan, overwrite=lambda item: True, language="es")
    text = _summary(workdir)
    assert text.startswith("# Resumen de ClearMD")
    assert "| Documento | Carpeta | Resultado | Formato | Tiempo |" in text


def test_ac_41_the_first_file_time_does_not_include_the_worker_start_up(workdir: Path) -> None:
    source = put(workdir, "sample.txt", "tiny.txt")
    assert main([str(source), "--quiet"]) == 0
    row = next(line for line in _summary(workdir).splitlines() if "`tiny.txt`" in line)
    assert row.endswith("| <1 s |")


def test_ac_28_a_summary_that_cannot_be_written_is_reported(
    workdir: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from clearmd.backend.services.summary.writer import MarkdownSummaryWriter

    def full_disk(self: object, report: object) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(MarkdownSummaryWriter, "write", full_disk)
    source = put(workdir, "sample.txt", "a.txt")
    assert main([str(source)]) == 0
    assert "could not be written" in capsys.readouterr().err
