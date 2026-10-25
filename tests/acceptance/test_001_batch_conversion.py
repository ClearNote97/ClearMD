"""Feature 001 — one test per acceptance criterion (spec/features/001_*/spec.md)."""

import json
import os
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
    message = "This PDF is password-protected. Remove the password and try again."
    assert message in capsys.readouterr().err


def _tree(root: Path) -> list[str]:
    return sorted(str(path.relative_to(root)) for path in root.rglob("*"))


def test_ac_02_a_folder_mirrors_its_structure(workdir: Path) -> None:
    project = workdir / "project"
    put(project, "sample.pdf", "a.pdf")
    put(project, "sample.docx", "sub/b.docx")
    put(project, "sample.txt", "sub/deeper/c.txt")
    (project / "only_unsupported").mkdir()
    (project / "only_unsupported" / "x.tex").write_text(
        "\\documentclass{article}", encoding="utf-8"
    )
    assert main([str(project), "--quiet"]) == 0
    output = workdir / "ClearMD_Output" / "OutputMD"
    assert _tree(output) == [
        "project",
        "project/a.md",
        "project/sub",
        "project/sub/b.md",
        "project/sub/deeper",
        "project/sub/deeper/c.md",
    ]


def test_ac_03_no_recursive_converts_only_the_top_level(workdir: Path) -> None:
    project = workdir / "project"
    put(project, "sample.txt", "top.txt")
    put(project, "sample.txt", "sub/inner.txt")
    assert main([str(project), "--no-recursive", "--quiet"]) == 0
    assert _tree(workdir / "ClearMD_Output" / "OutputMD") == ["project", "project/top.md"]


def test_ac_04_each_input_goes_to_its_own_output_root(workdir: Path) -> None:
    first = put(workdir / "one", "sample.txt", "a.txt")
    second = put(workdir / "two", "sample.txt", "b.txt")
    assert main([str(first), str(second), "--quiet"]) == 0
    assert (workdir / "one" / "ClearMD_Output" / "OutputMD" / "a.md").is_file()
    assert (workdir / "two" / "ClearMD_Output" / "OutputMD" / "b.md").is_file()


def test_ac_05_scanning_skips_output_folders_links_hidden_and_lock_files(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = workdir / "project"
    put(project, "sample.txt", "keep.txt")
    put(project, "sample.txt", "ClearMD_Output/OutputMD/old.txt")
    put(project, "sample.txt", ".hidden/a.txt")
    put(project, "sample.txt", ".hidden/b.txt")
    put(project, "sample.txt", ".dotfile.txt")
    put(project, "sample.docx", "~$lock.docx")
    os.symlink(project / "keep.txt", project / "link.txt")
    assert main([str(project)]) == 0
    assert _tree(workdir / "ClearMD_Output" / "OutputMD") == ["project", "project/keep.md"]
    err = capsys.readouterr().err
    assert err.count(".hidden") == 1  # a skipped folder is reported once
    for name in ("ClearMD_Output", ".dotfile.txt", "~$lock.docx", "link.txt"):
        assert name in err


def test_ac_06_missing_input_and_nothing_to_convert(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    present = put(workdir, "sample.txt", "a.txt")
    assert main([str(workdir / "missing.pdf"), str(present), "--quiet"]) == 0
    assert "missing.pdf" in capsys.readouterr().err
    empty = workdir / "empty"
    empty.mkdir()
    assert main([str(empty)]) == 0
    assert "Nothing to convert." in capsys.readouterr().out
    assert not (empty / "ClearMD_Output").exists()
    assert not (workdir / "ClearMD_Output" / "OutputMD" / "empty").exists()


def test_ac_07_files_over_250_mib_are_skipped(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    big = workdir / "huge.pdf"
    with big.open("wb") as handle:
        handle.truncate(251 * 1024**2)
    assert main([str(big)]) == 0
    assert "too large" in capsys.readouterr().err
    assert not (workdir / "ClearMD_Output").exists()


def test_ac_08_markdown_and_zip_are_skipped_with_their_reason(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (workdir / "notes.md").write_text("# hi", encoding="utf-8")
    (workdir / "bundle.zip").write_bytes(b"PK\x05\x06" + b"\x00" * 18)
    assert main([str(workdir / "notes.md"), str(workdir / "bundle.zip")]) == 0
    err = capsys.readouterr().err
    assert "already Markdown" in err
    assert "ZIP archives are not supported — extract them first" in err


def test_ac_09_a_zip_bomb_is_skipped_before_converting(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bomb = put(workdir, "zip_bomb.docx", "contract.docx")
    good = put(workdir, "sample.txt", "good.txt")
    assert main([str(bomb), str(good)]) == 0
    assert "this file looks damaged or unsafe" in capsys.readouterr().err
    assert not (workdir / "ClearMD_Output" / "OutputMD" / "contract.md").exists()
    assert (workdir / "ClearMD_Output" / "OutputMD" / "good.md").is_file()


def test_ac_10_documents_without_extension_are_detected_by_content(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(workdir, "docx_without_extension", "scan")
    put(workdir, "sample.txt", "README")
    put(workdir, "sample.docx", "report.dat")  # an extension ClearMD does not know: skipped
    arguments = [str(workdir / name) for name in ("scan", "README", "report.dat")]
    assert main(arguments) == 0
    output = workdir / "ClearMD_Output" / "OutputMD"
    assert MARKERS["sample.docx"] in (output / "scan.md").read_text(encoding="utf-8")
    assert MARKERS["sample.txt"] in (output / "README.md").read_text(encoding="utf-8")
    assert not (output / "report.md").exists()
    assert "report.dat — unsupported format" in capsys.readouterr().err


def test_ac_11_an_unsupported_file_is_skipped_and_the_batch_continues(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    script = workdir / "tool.py"
    script.write_text("import sys\n\ndef main():\n    print(sys.argv)\n", encoding="utf-8")
    good = put(workdir, "sample.txt", "good.txt")
    assert main([str(script), str(good)]) == 0
    assert "tool.py — unsupported format" in capsys.readouterr().err
    assert (workdir / "ClearMD_Output" / "OutputMD" / "good.md").is_file()
