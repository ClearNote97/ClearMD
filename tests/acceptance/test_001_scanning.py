"""Feature 001 — scanning the inputs: structure, skips and output roots."""

import os
from pathlib import Path

import pytest
from build_fixtures import MARKERS
from support import put
from support.batch_cli import _tree

from clearmd.frontend.cli import main


def test_ac_02_a_folder_mirrors_its_structure(workdir: Path) -> None:
    project = workdir / "project"
    put(project, "sample.pdf", "a.pdf")
    put(project, "sample.docx", "sub/b.docx")
    put(project, "sample.txt", "sub/deeper/c.txt")
    (project / "only_unsupported").mkdir()
    (project / "only_unsupported" / "refs.bib").write_text("@book{a, title={x}}", encoding="utf-8")
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
    assert main([str(project), "--no-recursive", "--quiet"]) == 0  # the flag wins over settings
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
    assert "Skipped: bundle.zip — ZIP archive. Extract it and convert its contents." in err


def test_ac_09_a_zip_bomb_is_skipped_before_converting(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bomb = put(workdir, "zip_bomb.docx", "contract.docx")
    good = put(workdir, "sample.txt", "good.txt")
    assert main([str(bomb), str(good)]) == 0
    # The check that failed, with the file's value and the limit, and what to do (UX §3).
    assert "Skipped: contract.docx — grows" in (err := capsys.readouterr().err)
    assert "limit 100 (possible zip bomb). If you trust it, save a new copy" in err
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
    assert "Skipped: report.dat — format not supported by ClearMD" in capsys.readouterr().err


def test_ac_11_an_unsupported_file_is_skipped_and_the_batch_continues(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    script = workdir / "tool.py"
    script.write_text("import sys\n\ndef main():\n    print(sys.argv)\n", encoding="utf-8")
    good = put(workdir, "sample.txt", "good.txt")
    assert main([str(script), str(good)]) == 0
    assert "Skipped: tool.py — format not supported by ClearMD" in capsys.readouterr().err
    assert (workdir / "ClearMD_Output" / "OutputMD" / "good.md").is_file()


def test_ac_12_the_home_folder_keeps_its_output_inside(
    workdir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = workdir / "ana"
    put(home, "sample.txt", "notes.txt")
    put(home, "sample.txt", "work/plan.txt")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    assert main([str(home), "--quiet"]) == 0
    assert _tree(home / "ClearMD_Output" / "OutputMD") == ["notes.md", "work", "work/plan.md"]


def test_ac_13_output_root_writes_into_the_chosen_folder(workdir: Path) -> None:
    single = put(workdir / "in", "sample.txt", "notes.txt")
    project = workdir / "in" / "project"
    put(project, "sample.txt", "a.txt")
    chosen = workdir / "chosen"
    assert main([str(single), str(project), "--output-root", str(chosen), "--quiet"]) == 0
    assert _tree(chosen / "ClearMD_Output" / "OutputMD") == ["notes.md", "project", "project/a.md"]
    assert not (workdir / "in" / "ClearMD_Output").exists()


def test_ac_14_colliding_outputs_get_the_extension_and_a_counter(workdir: Path) -> None:
    put(workdir, "sample.pdf", "report.pdf")
    put(workdir, "sample.docx", "Report.docx")
    other = put(workdir / "elsewhere", "sample.pdf", "report.pdf")
    chosen = workdir / "chosen"
    arguments = [str(workdir / "report.pdf"), str(workdir / "Report.docx"), str(other)]
    assert main([*arguments, "--output-root", str(chosen), "--quiet"]) == 0
    names = sorted(p.name for p in (chosen / "ClearMD_Output" / "OutputMD").iterdir())
    assert names == ["Report (docx).md", "report (pdf 2).md", "report (pdf).md"]


def test_ac_15_full_stems_and_unicode_names_are_kept(workdir: Path) -> None:
    first = put(workdir, "sample.txt", "report.v2.final.txt")
    second = put(workdir, "sample.docx", "informe_año_ñ.docx")
    assert main([str(first), str(second), "--quiet"]) == 0
    output = workdir / "ClearMD_Output" / "OutputMD"
    assert sorted(p.name for p in output.iterdir()) == ["informe_año_ñ.md", "report.v2.final.md"]
