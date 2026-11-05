"""A real batch through the window (005, AC-20)."""

from pathlib import Path

from support.gui_close import shut
from support.gui_fakes import MemoryBackend
from support.ttk_unit import confirm, pump

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter import AppState
from clearmd.frontend.ttk import TtkApp

# --- A real batch through the window (AC-20) -----------------------------------------------------

FIXTURES = Path(__file__).resolve().parents[4] / "fixtures" / "documents"


def test_a_real_batch_through_the_window_writes_the_markdown(display: str, tmp_path: Path) -> None:
    folder = tmp_path / "Documentos"
    folder.mkdir()
    for name in ("sample.docx", "sample.csv", "sample.txt", "encrypted.pdf"):
        (folder / name).write_bytes((FIXTURES / name).read_bytes())
    (folder / "notas.md").write_text("# ya es Markdown\n", encoding="utf-8")
    backend = MemoryBackend(Settings(show_welcome=False))
    app = TtkApp(backend)
    try:
        app.start()
        app.presenter.add_paths([folder])
        app.actions.primary.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION, seconds=30)
        assert app.review.stats.figures()[:2] == [("To convert", "4"), ("Skipped", "1")]
        confirm(app)
        finished = {AppState.FINISHED, AppState.FINISHED_WITH_PROBLEMS}
        pump(app, until=lambda: app.presenter.state in finished, seconds=120)
        assert app.presenter.state is AppState.FINISHED_WITH_PROBLEMS  # the encrypted PDF
        assert app.last_result is not None
        (output,) = app.last_result.folders  # ClearMD_Output, next to the chosen folder
        assert output == tmp_path / "ClearMD_Output"
        assert len(list(output.rglob("*.md"))) == 4  # three documents and the summary
        assert set(app.results.problems.names()) == {"encrypted.pdf", "notas.md"}
        assert backend.opened == [output]
    finally:
        shut(app)
