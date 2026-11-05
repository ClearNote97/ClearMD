"""Feature 001 — converting files: failures, limits and ordering."""

import json
import random
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from benchlib.common import SEED
from benchlib.pdf import make_pdf
from builders.common import MARKERS
from support import WINDOWS, put

from clearmd.backend.api import composition
from clearmd.frontend.cli import main


def test_ac_01_a_file_converts_into_clearmd_output(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = put(workdir, "sample.pdf", "report.pdf")
    assert main([str(source)]) == 0
    output = workdir / "ClearMD_Output" / "OutputMD" / "report.md"
    data = output.read_bytes()
    assert b"\r\n" not in data
    assert MARKERS["sample.pdf"] in data.decode("utf-8")
    assert "1 converted" in capsys.readouterr().out


def test_ac_19_the_cli_process_never_imports_markitdown_or_magika(workdir: Path) -> None:
    source = put(workdir, "sample.docx", "notes.docx")
    scan = put(workdir, "docx_without_extension", "scan")  # content detection runs in the worker
    script = (
        "import json, sys\n"
        "from clearmd.frontend.cli import main\n"
        f"code = main([{str(source)!r}, {str(scan)!r}, '--quiet'])\n"
        "print(json.dumps({'code': code, 'loaded': sorted(m for m in ('markitdown', 'magika')"
        " if m in sys.modules)}))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True, timeout=120
    )
    report = json.loads(result.stdout.strip().splitlines()[-1])
    assert report == {"code": 0, "loaded": []}
    assert (workdir / "ClearMD_Output" / "OutputMD" / "notes.md").is_file()


def test_ac_21_a_failed_file_does_not_stop_the_batch(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    broken = put(workdir, "corrupt.docx", "broken.docx")
    good = put(workdir, "sample.txt", "good.txt")
    assert main([str(broken), str(good)]) == 1
    assert (workdir / "ClearMD_Output" / "OutputMD" / "good.md").is_file()
    assert not (workdir / "ClearMD_Output" / "OutputMD" / "broken.md").exists()
    captured = capsys.readouterr()
    assert "This file seems to be damaged." in captured.err
    assert "1 failed" in captured.out


def test_ac_22_password_protected_pdf_has_a_human_message(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = put(workdir, "encrypted.pdf", "contract.pdf")
    assert main([str(source)]) == 1
    message = "This file is password-protected. Remove the password and try again."
    assert message in capsys.readouterr().err


def _progress_names(err: str) -> list[str]:
    lines = [line for line in err.splitlines() if line.startswith("[")]
    return [line.split("] ", 1)[1].split(" · ")[0] for line in lines]


def test_ac_20_files_are_converted_from_the_cheapest(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(workdir, "sample.pdf", "a_report.pdf")  # PDF: the slowest per MiB
    put(workdir, "sample.txt", "z_notes.txt")
    put(workdir, "sample.docx", "m_letter.docx")
    assert main([str(workdir)]) == 0
    # 41 bytes of text, ~1.5 KB of docx XML, then the PDF (the slowest per MiB), whatever the names.
    expected = ["z_notes.txt", "m_letter.docx", "a_report.pdf"]
    assert _progress_names(capsys.readouterr().err) == expected


def test_ac_40_the_time_left_appears_from_the_second_file(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    for name in ("a", "b", "c"):
        put(workdir, "sample.txt", f"{name}.txt")
    assert main([str(workdir)]) == 0
    lines = [line for line in capsys.readouterr().err.splitlines() if line.startswith("[")]
    assert " · " not in lines[0]
    assert all(" · " in line and "left" in line for line in lines[1:])


def test_ac_42_a_file_that_would_not_fit_in_memory_is_skipped_before_converting(
    workdir: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    put(workdir, "sample.xlsx", "sales.xlsx")
    tiny = replace(composition.default_limits(), worker_memory=100 * 1024**2)
    monkeypatch.setattr(composition, "default_limits", lambda: tiny)
    assert main([str(workdir / "sales.xlsx")]) == 0
    err = capsys.readouterr().err
    assert "Skipped: sales.xlsx — needs about" in err
    assert "of memory; limit 100 MB. Split it into smaller files." in err
    assert not (workdir / "ClearMD_Output").exists()


def test_ac_43_a_file_that_may_take_too_long_is_warned_about_and_still_tried(
    workdir: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    put(workdir, "sample.txt", "quick.txt")
    put(workdir, "sample.pdf", "manual.pdf")
    # The PDF's estimate (~0.01 s, ADR-0030) exceeds this limit; the tiny text file's does not.
    limits = replace(composition.default_limits(), time_per_file=0.005)
    monkeypatch.setattr(composition, "default_limits", lambda: limits)
    main([str(workdir)])
    err = capsys.readouterr().err
    assert "⚠ manual.pdf — may take more than" in err
    assert _progress_names(err)[-1] == "manual.pdf"


def test_ac_23_and_ac_44_a_file_over_the_time_limit_is_stopped_not_failed(
    workdir: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    put(workdir, "sample.txt", "quick.txt")
    # ~300 text pages: ~4 s for PDFium and ClearMD's cleaning (ADR-0030), well over a 0.5 s
    # limit (the supervisor polls every 0.1 s).
    make_pdf(workdir / "manual.pdf", 1024 * 1024, random.Random(SEED))
    limits = replace(composition.default_limits(), time_per_file=0.5)
    monkeypatch.setattr(composition, "default_limits", lambda: limits)
    assert main([str(workdir / "quick.txt"), str(workdir / "manual.pdf")]) == 1
    captured = capsys.readouterr()
    assert "⏹ Stopped: manual.pdf — Exceeded the time limit" in captured.err
    assert "after 0:00" in captured.err
    assert not (workdir / "ClearMD_Output" / "OutputMD" / "manual.md").exists()
    assert (workdir / "ClearMD_Output" / "OutputMD" / "quick.md").is_file()
    assert "Try splitting it into smaller files." in captured.err
    assert "stopped" in captured.out


@pytest.mark.skipif(WINDOWS, reason="chmod cannot make a folder unwritable on Windows")
def test_ac_27_an_unwritable_output_root_fails_its_files_and_others_continue(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    locked = workdir / "locked"
    source = put(locked, "sample.txt", "a.txt")
    other = put(workdir / "free", "sample.txt", "b.txt")
    locked.chmod(0o555)
    try:
        assert main([str(source), str(other)]) == 1
    finally:
        locked.chmod(0o755)
    err = capsys.readouterr().err
    assert "ClearMD cannot write in this folder. Choose another output folder." in err
    assert "--output-root" in err
    assert (workdir / "free" / "ClearMD_Output" / "OutputMD" / "b.md").is_file()
