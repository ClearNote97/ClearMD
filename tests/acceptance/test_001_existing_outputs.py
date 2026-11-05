"""Feature 001 — existing outputs and interruption (spec/features/001_*/spec.md)."""

import random
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest
from benchlib.common import SEED
from benchlib.pdf import make_pdf
from support import WINDOWS, put

from clearmd.frontend.cli import main


def _with_existing_outputs(workdir: Path) -> tuple[Path, Path]:
    first = put(workdir, "sample.txt", "a.txt")
    second = put(workdir, "sample.txt", "b.txt")
    assert main([str(first), str(second), "--quiet"]) == 0
    for name in ("a", "b"):
        (workdir / "ClearMD_Output" / "OutputMD" / f"{name}.md").write_text("old", encoding="utf-8")
    return first, second


def _outputs(workdir: Path) -> dict[str, str]:
    folder = workdir / "ClearMD_Output" / "OutputMD"
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted(folder.glob("*.md"))}


@pytest.mark.parametrize(
    ("answers", "expected"),
    [
        (["1"], {"a": "new", "b": "new"}),
        (["2"], {"a": "old", "b": "old"}),
        (["3", "y", "n"], {"a": "new", "b": "old"}),
        (["9", "x", "?"], {"a": "old", "b": "old"}),  # no valid answer: the safe choice
        ([], {"a": "old", "b": "old"}),  # end of input: the safe choice
    ],
)
def test_ac_16_existing_outputs_are_asked_about_once(
    workdir: Path, monkeypatch: pytest.MonkeyPatch, answers: list[str], expected: dict[str, str]
) -> None:
    from clearmd.frontend.cli import prompts

    first, second = _with_existing_outputs(workdir)
    replies = iter(answers)
    monkeypatch.setattr(prompts, "is_interactive", lambda: True)
    monkeypatch.setattr(prompts, "ask", lambda prompt: next(replies, None))
    assert main([str(first), str(second), "--quiet"]) == 0
    got = {name: ("old" if text == "old" else "new") for name, text in _outputs(workdir).items()}
    assert got == expected


def test_ac_17_overwrite_and_skip_together_are_a_usage_error(workdir: Path) -> None:
    source = put(workdir, "sample.txt", "a.txt")
    with pytest.raises(SystemExit) as exit_info:
        main([str(source), "--overwrite", "--skip"])
    assert exit_info.value.code == 2


def test_ac_18_no_terminal_no_flag_means_exit_3_and_nothing_written(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    first, second = _with_existing_outputs(workdir)
    capsys.readouterr()
    assert main([str(first), str(second)]) == 3
    assert "--overwrite or --skip" in capsys.readouterr().err
    assert _outputs(workdir) == {"a": "old", "b": "old"}


@pytest.mark.skipif(
    WINDOWS, reason="Ctrl+C is a POSIX signal here; on Windows the console sends its own event"
)
def test_ac_26_ctrl_c_stops_at_once_and_still_writes_the_summary(workdir: Path) -> None:
    quick = put(workdir, "sample.txt", "quick.txt")
    slow = workdir / "slow.pdf"
    make_pdf(slow, 2 * 1024 * 1024, random.Random(SEED))  # ~9 s of PDFium and cleaning
    script = "import sys\nfrom clearmd.frontend.cli import main\nsys.exit(main(sys.argv[1:]))\n"
    process = subprocess.Popen(
        [sys.executable, "-c", script, str(quick), str(slow)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stderr is not None
    seen = ""
    deadline = time.monotonic() + 60
    while "[2/2]" not in seen and time.monotonic() < deadline:
        seen += process.stderr.readline()
    time.sleep(0.5)  # the slow PDF is being converted now
    began = time.monotonic()
    process.send_signal(signal.SIGINT)
    _, err = process.communicate(timeout=60)
    assert process.returncode == 130, seen + err
    assert time.monotonic() - began < 5  # at once, not after the 8 s file
    output = workdir / "ClearMD_Output"
    assert (output / "OutputMD" / "quick.md").is_file()
    assert not (output / "OutputMD" / "slow.md").exists()
    assert list(output.rglob("*.clearmd-tmp")) == []
    summary = (output / "Resumen_ClearMD.md").read_text(encoding="utf-8")
    assert "## Cancelled\n- ⏹️ `slow.pdf`" in summary


def test_ac_26_ctrl_c_at_the_question_exits_130_and_writes_nothing_new(
    workdir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from clearmd.frontend.cli import prompts

    first, second = _with_existing_outputs(workdir)

    def interrupted(prompt: str) -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr(prompts, "is_interactive", lambda: True)
    monkeypatch.setattr(prompts, "ask", interrupted)
    assert main([str(first), str(second), "--quiet"]) == 130
    assert _outputs(workdir) == {"a": "old", "b": "old"}
