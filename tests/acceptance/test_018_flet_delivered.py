"""Feature 018 — A batch converted through the flet window gives the CLI's Markdown (AC-08);
spec/features/018_*/spec.md. The window is built on a page that is not flet's, on the real backend.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from support.flet_acceptance import (
    QUIET,
    Window,
    confirm,
    converted,
    copy_documents,
    pump,
    to_review,
    windows,
)
from support.gui_fakes import MemoryBackend

from clearmd.frontend.cli import main as cli_main


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def test_ac_08_the_flet_window_converts_like_the_cli(flet_window: Window, tmp_path: Path) -> None:
    names = ("sample.docx", "sample.csv", "sample.txt", "encrypted.pdf")
    by_gui = copy_documents(tmp_path / "gui" / "Docs", *names)
    by_cli = copy_documents(tmp_path / "cli" / "Docs", *names)
    app = flet_window(MemoryBackend(QUIET))
    to_review(app, by_gui)
    confirm(app)
    pump(app, until=lambda: converted(app), seconds=120)
    assert converted(app)
    cli_main([str(by_cli), "--quiet"])

    def outputs(root: Path) -> dict[str, str]:
        out = root / "ClearMD_Output" / "OutputMD"
        return {str(p.relative_to(out)): p.read_text(encoding="utf-8") for p in out.rglob("*.md")}

    assert outputs(tmp_path / "gui") == outputs(tmp_path / "cli") != {}
    summaries = [
        (root / "ClearMD_Output" / "Resumen_ClearMD.md").read_text(encoding="utf-8")
        for root in (tmp_path / "gui", tmp_path / "cli")
    ]
    tables = [[line for line in text.splitlines() if line.startswith("| `")] for text in summaries]
    assert tables[0] == tables[1] != []
    assert app.results.stats.figures()[0] == ("Converted", "3")  # and the window says so
    assert "password" in str(app.results.detail.value)  # the encrypted one, in its words
