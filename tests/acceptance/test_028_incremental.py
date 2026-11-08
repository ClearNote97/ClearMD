"""Feature 028 — Incremental mode (spec/features/028_*/spec.md): "Replace it if the original
changed", through the command line and the presenter."""

import os
import time
from dataclasses import replace
from pathlib import Path

import pytest
from support.gui_fakes import FakeBackend, planned
from support.presenter_fakes import make

from clearmd.backend.api import changed_since_result
from clearmd.backend.schemas.settings import CHOICES, Settings
from clearmd.frontend.cli import main
from clearmd.frontend.presenter.intents.conversion import existing_decision
from clearmd.i18n import load_catalog


def age(path: Path, seconds: float) -> None:
    """Make ``path`` look written ``seconds`` ago."""
    when = time.time() - seconds
    os.utime(path, (when, when))


def two_converted(workdir: Path) -> tuple[Path, Path]:
    docs = workdir / "docs"
    docs.mkdir()
    for name in ("a.txt", "b.txt"):
        (docs / name).write_text(f"{name} first\n", "utf-8")
    assert main([str(docs), "--quiet"]) == 0
    results = workdir / "ClearMD_Output" / "OutputMD" / "docs"
    for name in ("a.txt", "b.txt"):  # the originals older than their results
        age(docs / name, 3600)
    return docs, results


def test_ac_01_only_what_changed_is_converted_again(workdir: Path) -> None:
    docs, results = two_converted(workdir)
    (docs / "b.txt").write_text("b.txt edited\n", "utf-8")  # newer than its result now
    (docs / "c.txt").write_text("c.txt new\n", "utf-8")
    before = (results / "a.md").stat().st_mtime_ns
    assert main([str(docs), "--quiet", "--changed"]) == 0
    assert (results / "a.md").stat().st_mtime_ns == before  # unchanged: kept
    assert "edited" in (results / "b.md").read_text("utf-8")
    assert (results / "c.md").is_file()  # new: converted as always


def test_ac_02_a_split_files_parts_follow_the_same_rule(workdir: Path) -> None:
    source = workdir / "notes.txt"
    source.write_text("".join(f"line {n}\n" for n in range(20)), "utf-8")
    assert main([str(source), "--quiet", "--split-parts", "2", "--keep", "pdf"]) == 0
    folder = workdir / "ClearMD_Output" / "OutputSep" / "notes"
    age(source, 3600)
    assert not changed_since_result(replace(planned("notes.txt"), source=source, target=folder))
    source.write_text("changed\n" * 3, "utf-8")
    assert main([str(source), "--quiet", "--split-parts", "2", "--keep", "pdf", "--changed"]) == 0
    assert "changed" in "".join(path.read_text("utf-8") for path in folder.iterdir())


def test_ac_03_the_flag_and_the_setting(workdir: Path) -> None:
    assert "changed" in CHOICES["on_existing_output"]
    source = workdir / "a.txt"
    source.write_text("x\n", "utf-8")
    with pytest.raises(SystemExit) as stop:
        main([str(source), "--changed", "--overwrite"])
    assert stop.value.code == 2


def test_ac_04_the_presenter_passes_the_rule_on() -> None:
    assert existing_decision("changed", None) is changed_since_result
    assert existing_decision("ask", "changed") is changed_since_result
    assert existing_decision("ask", True)(planned("a.pdf")) is True
    presenter, view, fake, _ = make(FakeBackend(settings=Settings(on_existing_output="changed")))
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    presenter.confirm()
    view.drain()
    assert fake.run_calls[-1]["overwrite"] is changed_since_result


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_05_texts_in_both_languages(language: str) -> None:
    catalog = load_catalog(language)
    for key in ("gui.settings.existing_changed", "gui.plan.changed", "cli.help.changed"):
        assert catalog.text_template(key)
