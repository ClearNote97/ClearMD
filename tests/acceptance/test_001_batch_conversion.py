"""Feature 001 — one test per acceptance criterion (spec/features/001_*/spec.md)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from build_fixtures import MARKERS
from support import put

from clearmd.frontend.cli import main


def test_ac_01_a_file_converts_into_clearmd_output(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = put(workdir, "sample.pdf", "report.pdf")
    assert main([str(source)]) == 0
    output = workdir / "ClearMD_Output" / "Output" / "report.md"
    data = output.read_bytes()
    assert b"\r\n" not in data
    assert MARKERS["sample.pdf"] in data.decode("utf-8")
    assert "1 converted" in capsys.readouterr().out


def test_ac_19_the_cli_process_never_imports_markitdown_or_magika(workdir: Path) -> None:
    source = put(workdir, "sample.docx", "notes.docx")
    script = (
        "import json, sys\n"
        "from clearmd.frontend.cli import main\n"
        f"code = main([{str(source)!r}, '--quiet'])\n"
        "print(json.dumps({'code': code, 'loaded': sorted(m for m in ('markitdown', 'magika')"
        " if m in sys.modules)}))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True, timeout=120
    )
    report = json.loads(result.stdout.strip().splitlines()[-1])
    assert report == {"code": 0, "loaded": []}
    assert (workdir / "ClearMD_Output" / "Output" / "notes.md").is_file()


def test_ac_21_a_failed_file_does_not_stop_the_batch(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    broken = put(workdir, "corrupt.docx", "broken.docx")
    good = put(workdir, "sample.txt", "good.txt")
    assert main([str(broken), str(good)]) == 1
    assert (workdir / "ClearMD_Output" / "Output" / "good.md").is_file()
    assert not (workdir / "ClearMD_Output" / "Output" / "broken.md").exists()
    captured = capsys.readouterr()
    assert "This file seems to be damaged." in captured.err
    assert "1 failed" in captured.out


def test_ac_22_password_protected_pdf_has_a_human_message(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = put(workdir, "encrypted.pdf", "contract.pdf")
    assert main([str(source)]) == 1
    message = "This PDF is password-protected. Remove the password and try again."
    assert message in capsys.readouterr().err
