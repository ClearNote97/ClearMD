"""Feature 001 — the command line: language, exit codes and what it prints."""

from pathlib import Path

import pytest
from support import WINDOWS, put
from support.batch_cli import _settings, _summary

from clearmd.frontend.cli import main
from clearmd.i18n import load_catalog


def test_ac_31_messages_follow_lang(workdir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = put(workdir, "sample.txt", "notas.txt")
    assert main([str(source), "--lang", "es"]) == 0
    captured = capsys.readouterr()
    assert "1 convertido · 0 omitidos · 0 con error" in captured.out  # singular (feature 009)
    assert "Resultados:" in captured.out
    assert _summary(workdir).startswith("# Resumen de ClearMD")


def test_ac_31_the_language_setting_is_used_without_lang(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _settings('language = "es"\n')
    source = put(workdir, "sample.txt", "notas.txt")
    assert main([str(source)]) == 0
    assert "1 convertido · " in capsys.readouterr().out


def test_ac_35_exit_codes(workdir: Path) -> None:
    good = put(workdir, "sample.txt", "good.txt")
    broken = put(workdir, "corrupt.docx", "broken.docx")
    assert main([str(good), "--quiet"]) == 0
    assert main([str(broken), "--quiet"]) == 1
    assert main([str(workdir / "missing.pdf"), "--quiet"]) == 2
    assert main([str(good), "--quiet"]) == 3  # existing output, no terminal, no flag


def test_ac_36_open_shows_the_results_folder_only_when_asked(
    workdir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from clearmd.frontend.cli import flow

    opened: list[Path] = []
    monkeypatch.setattr(flow, "open_folder", opened.append)
    source = put(workdir, "sample.txt", "a.txt")
    assert main([str(source), "--quiet"]) == 0
    assert opened == []
    assert main([str(source), "--overwrite", "--open", "--quiet"]) == 0
    assert opened == [workdir / "ClearMD_Output"]


def test_ac_37_dry_run_shows_the_plan_and_writes_nothing(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = put(workdir, "sample.txt", "a.txt")
    (workdir / "notes.md").write_text("# hi", encoding="utf-8")
    assert main([str(source), str(workdir / "notes.md"), "--dry-run"]) == 0
    captured = capsys.readouterr()
    assert "a.txt → " in captured.out and str(Path("OutputMD/a.md")) in captured.out
    assert "notes.md — already Markdown" in captured.err
    assert "nothing was written" in captured.out
    assert not (workdir / "ClearMD_Output").exists()


def test_ac_38_quiet_shows_only_the_summary_and_errors(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    good = put(workdir, "sample.txt", "good.txt")
    broken = put(workdir, "corrupt.docx", "broken.docx")
    (workdir / "notes.md").write_text("# hi", encoding="utf-8")
    assert main([str(good), str(broken), str(workdir / "notes.md"), "--quiet"]) == 1
    captured = capsys.readouterr()
    assert "[1/" not in captured.err  # no progress
    assert "notes.md" not in captured.err  # no skip notes
    assert "broken.docx — This file seems to be damaged." in captured.err
    assert "converted" in captured.out


def test_ac_30_the_cli_ends_with_counts_and_the_output_folders(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    first = put(workdir / "one", "sample.txt", "a.txt")
    second = put(workdir / "two", "corrupt.docx", "b.docx")
    (workdir / "one" / "c.md").write_text("# hi", encoding="utf-8")
    main([str(first), str(second), str(workdir / "one" / "c.md")])
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "1 converted · 1 skipped · 1 failed"
    assert out[1:] == [
        f"Results: {workdir / 'one' / 'ClearMD_Output'}",
        f"Results: {workdir / 'two' / 'ClearMD_Output'}",
    ]


def test_ac_32_both_catalogs_have_the_same_keys_and_placeholders() -> None:
    import string

    def placeholders(text: str) -> set[str]:
        return {name for _, name, _, _ in string.Formatter().parse(text) if name}

    english, spanish = load_catalog("en"), load_catalog("es")
    assert english.keys() == spanish.keys()
    for key in english.keys():
        assert placeholders(english.text_template(key)) == placeholders(spanish.text_template(key))


@pytest.mark.skipif(WINDOWS, reason="Windows file names cannot hold control characters")
def test_ac_38_control_characters_in_names_cannot_drive_the_terminal(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    name = "\x1b]0;owned\x07evil\u202e.txt"
    source = put(workdir, "sample.txt", name)
    assert main([str(source)]) == 0
    err = capsys.readouterr().err
    assert "\x1b" not in err and "\x07" not in err and "\u202e" not in err
    assert "\\x1b]0;owned\\x07evil\\u202e.txt" in err


def test_ac_35_an_unexpected_error_is_a_message_not_a_traceback(
    workdir: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from clearmd.frontend.cli import flow

    def broken(*args: object, **kwargs: object) -> None:
        raise RuntimeError("something nobody expected")

    monkeypatch.setattr(flow, "plan_batch", broken)
    source = put(workdir, "sample.txt", "a.txt")
    assert main([str(source)]) == 1
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert "RuntimeError: something nobody expected" in err


def test_ac_36_open_tells_a_folder_it_cannot_open_and_ends_normally(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = put(workdir, "sample.txt", "a.txt")
    (workdir / "elsewhere").mkdir()
    (workdir / "ClearMD_Output").symlink_to(workdir / "elsewhere")  # refused as a link
    code = main([str(source), "--open", "--quiet"])
    captured = capsys.readouterr()
    assert code == 1  # the file failed: the output folder is a link
    assert "Traceback" not in captured.err


def test_ac_36_open_shows_the_summary_even_when_every_file_failed(
    workdir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from clearmd.frontend.cli import flow

    opened: list[Path] = []
    monkeypatch.setattr(flow, "open_folder", opened.append)
    broken = workdir / "broken.pdf"
    broken.write_bytes(b"%PDF-1.4 not really")
    main([str(broken), "--open", "--quiet"])
    assert opened == [workdir / "ClearMD_Output"]  # its summary says why
