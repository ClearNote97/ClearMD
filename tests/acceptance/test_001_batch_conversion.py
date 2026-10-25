"""Feature 001 — one test per acceptance criterion (spec/features/001_*/spec.md)."""

import json
import os
import random
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from build_fixtures import MARKERS
from run_benchmark import SEED, make_pdf
from support import put

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
    assert "sales.xlsx — too big to convert (it would need about" in err
    assert "the limit is 0.1 GB" in err
    assert not (workdir / "ClearMD_Output").exists()


def test_ac_43_a_file_that_may_take_too_long_is_warned_about_and_still_tried(
    workdir: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    put(workdir, "sample.txt", "quick.txt")
    put(workdir, "sample.pdf", "manual.pdf")
    # The PDF's estimate (~0.02 s) exceeds this limit; the tiny text file's does not.
    limits = replace(composition.default_limits(), time_per_file=0.015)
    monkeypatch.setattr(composition, "default_limits", lambda: limits)
    main([str(workdir)])
    err = capsys.readouterr().err
    assert "⚠ manual.pdf — may take more than" in err
    assert _progress_names(err)[-1] == "manual.pdf"


def test_ac_23_and_ac_44_a_file_over_the_time_limit_is_stopped_not_failed(
    workdir: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    put(workdir, "sample.txt", "quick.txt")
    # ~30 text pages: ~3 s for pdfminer, well over a 0.5 s limit (the supervisor polls every 0.1 s).
    make_pdf(workdir / "manual.pdf", 100 * 1024, random.Random(SEED))
    limits = replace(composition.default_limits(), time_per_file=0.5)
    monkeypatch.setattr(composition, "default_limits", lambda: limits)
    assert main([str(workdir / "quick.txt"), str(workdir / "manual.pdf")]) == 1
    captured = capsys.readouterr()
    assert "⏹ manual.pdf — stopped after 0:00 (about" in captured.err
    assert not (workdir / "ClearMD_Output" / "OutputMD" / "manual.md").exists()
    assert (workdir / "ClearMD_Output" / "OutputMD" / "quick.md").is_file()
    assert "Try splitting it into smaller files." in captured.err
    assert "stopped" in captured.out


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


def _summary(folder: Path) -> str:
    return (folder / "ClearMD_Output" / "Resumen_ClearMD.md").read_text(encoding="utf-8")


def test_ac_22_and_ac_28_each_output_root_gets_its_summary(workdir: Path) -> None:
    good = put(workdir / "one", "sample.txt", "notes.txt")
    broken = put(workdir / "one", "corrupt.docx", "broken.docx")
    scan = put(workdir / "one", "docx_without_extension", "scan")
    other = put(workdir / "two", "sample.txt", "other.txt")
    (workdir / "one" / "old.md").write_text("# hi", encoding="utf-8")
    arguments = [str(good), str(broken), str(scan), str(other), str(workdir / "one" / "old.md")]
    assert main([*arguments, "--quiet"]) == 1
    one = _summary(workdir / "one")
    assert "| `notes.txt` | `OutputMD/notes.md` | TXT |" in one
    assert "| `scan` | `OutputMD/scan.md` | DOCX, detected by content |" in one
    assert "- `broken.docx` — This file seems to be damaged." in one
    assert "<details><summary>Technical detail</summary>BadZipFile" in one
    assert "- `old.md` — already Markdown" in one
    assert "other.txt" not in one
    assert "`other.txt`" in _summary(workdir / "two")


def test_ac_29_the_history_keeps_earlier_batches(workdir: Path) -> None:
    source = put(workdir, "sample.txt", "notes.txt")
    assert main([str(source), "--quiet"]) == 0
    first_header = _summary(workdir).splitlines()[1]
    assert main([str(source), "--overwrite", "--quiet"]) == 0
    history = _summary(workdir).split("## History", 1)[1]
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
    assert "| Origen | Resultado | Formato | Tiempo |" in text


def test_ac_41_the_first_file_time_does_not_include_the_worker_start_up(workdir: Path) -> None:
    source = put(workdir, "sample.txt", "tiny.txt")
    assert main([str(source), "--quiet"]) == 0
    row = next(line for line in _summary(workdir).splitlines() if "`tiny.txt`" in line)
    assert row.endswith("| <1 s |")


def _settings(text: str) -> None:
    from clearmd.backend.api import settings_path

    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_ac_03_the_recursive_setting_is_honored(workdir: Path) -> None:
    _settings("recursive = false\n")
    project = workdir / "project"
    put(project, "sample.txt", "top.txt")
    put(project, "sample.txt", "sub/inner.txt")
    assert main([str(project), "--quiet"]) == 0
    assert _tree(workdir / "ClearMD_Output" / "OutputMD") == ["project", "project/top.md"]


def test_ac_18_the_existing_output_setting_applies_without_asking(workdir: Path) -> None:
    source = put(workdir, "sample.txt", "notes.txt")
    assert main([str(source), "--quiet"]) == 0
    output = workdir / "ClearMD_Output" / "OutputMD" / "notes.md"
    output.write_text("edited by hand", encoding="utf-8")
    _settings('on_existing_output = "skip"\n')
    assert main([str(source), "--quiet"]) == 0
    assert output.read_text(encoding="utf-8") == "edited by hand"
    _settings('on_existing_output = "overwrite"\n')
    assert main([str(source), "--quiet"]) == 0
    assert output.read_text(encoding="utf-8") != "edited by hand"


def test_ac_33_a_broken_or_invalid_settings_file_never_stops_the_app(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = put(workdir, "sample.txt", "notes.txt")
    _settings('language = "fr"\ncolour = "blue"\n')
    assert main([str(source), "--quiet"]) == 0
    err = capsys.readouterr().err
    assert "invalid value for “language”" in err
    assert "unknown setting “colour”" in err
    _settings('language = "es\n')
    assert main([str(source), "--overwrite", "--quiet"]) == 0
    assert "settings.toml could not be read" in capsys.readouterr().err


def test_ac_34_flags_override_settings_for_that_run_only(workdir: Path) -> None:
    _settings("recursive = false\n")
    project = workdir / "project"
    put(project, "sample.txt", "sub/inner.txt")
    assert main([str(project), "--recursive", "--quiet"]) == 0
    assert (workdir / "ClearMD_Output" / "OutputMD" / "project" / "sub" / "inner.md").is_file()
