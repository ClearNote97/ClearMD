"""Feature 020 — the summary as a PDF alone (spec/features/020_*/spec.md): real batches through the
command line, the folder read back; the third choice on the three windows."""

import shutil
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from support import DOCUMENTS_DIR
from support.flet_acceptance import QUIET, windows
from support.gui_fakes import MemoryBackend
from support.presenter_fakes import make

from clearmd.backend.api import composition
from clearmd.backend.schemas.settings import CHOICES, Settings
from clearmd.frontend.cli import main
from clearmd.frontend.flet import FletApp
from clearmd.frontend.pyside import PySideApp
from clearmd.frontend.ttk import TtkApp

ROOT = Path(__file__).resolve().parents[2]


def put(workdir: Path, name: str) -> None:
    folder = workdir / "docs"
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DOCUMENTS_DIR / "sample.txt", folder / name)


def summaries(workdir: Path) -> set[str]:
    return {path.name for path in (workdir / "ClearMD_Output").glob("Resumen_ClearMD.*")}


def test_ac_01_pdf_only_writes_the_pdf_and_no_markdown(workdir: Path) -> None:
    put(workdir, "a.txt")
    assert main([str(workdir / "docs"), "--quiet", "--summary-pdf-only"]) == 0
    assert summaries(workdir) == {"Resumen_ClearMD.pdf"}
    data = (workdir / "ClearMD_Output" / "Resumen_ClearMD.pdf").read_bytes()
    assert data.startswith(b"%PDF")


def test_ac_02_an_earlier_markdown_summary_does_not_stay_beside_it(workdir: Path) -> None:
    put(workdir, "a.txt")
    main([str(workdir / "docs"), "--quiet"])
    assert summaries(workdir) == {"Resumen_ClearMD.md"}
    put(workdir, "b.txt")
    main([str(workdir / "docs"), "--quiet", "--overwrite", "--summary-pdf-only"])
    assert summaries(workdir) == {"Resumen_ClearMD.pdf"}
    main([str(workdir / "docs"), "--quiet", "--overwrite"])  # and back: the PDF goes
    assert summaries(workdir) == {"Resumen_ClearMD.md"}


def test_ac_03_if_the_pdf_cannot_be_written_the_markdown_is_and_it_is_told(
    workdir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class Broken:
        def write(self, report: object) -> None:
            raise OSError("disk full")

    monkeypatch.setattr(composition, "build_pdf_report", lambda language: Broken())
    put(workdir, "a.txt")
    assert main([str(workdir / "docs"), "--summary-pdf-only"]) == 0
    assert summaries(workdir) == {"Resumen_ClearMD.md"}  # never no summary at all
    assert "The PDF summary in" in capsys.readouterr().err


def test_ac_04_the_setting_decides_and_the_flags_override_it(
    workdir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import clearmd.frontend.cli.flow as cli

    assert "pdf" in CHOICES["summary_format"]
    monkeypatch.setattr(cli, "load_settings", lambda: (Settings(summary_format="pdf"), ()))
    put(workdir, "a.txt")
    main([str(workdir / "docs"), "--quiet"])
    assert summaries(workdir) == {"Resumen_ClearMD.pdf"}  # the setting
    main([str(workdir / "docs"), "--quiet", "--overwrite", "--summary-pdf"])
    assert summaries(workdir) == {"Resumen_ClearMD.md", "Resumen_ClearMD.pdf"}  # the flag
    main([str(workdir / "docs"), "--quiet", "--overwrite", "--no-summary-pdf"])
    assert summaries(workdir) == {"Resumen_ClearMD.md"}


def test_ac_05_the_presenter_asks_the_backend_for_the_pdf_alone() -> None:
    presenter, view, fake, _ = make()
    presenter.choose_summary_format("pdf")
    assert fake.settings.summary_format == "pdf" and view.last("output").summary_format == "pdf"
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    presenter.go_to(3)
    presenter.press_primary(False)
    view.drain()
    assert fake.run_calls[-1]["summary_pdf"] is True
    assert fake.run_calls[-1]["summary_markdown"] is False


@pytest.fixture
def flet_window() -> Iterator[Callable[..., FletApp]]:
    yield from windows()


def test_ac_06_the_third_choice_on_the_three_windows(
    window: Callable[..., TtkApp],
    qt_window: Callable[..., PySideApp],
    flet_window: Callable[..., FletApp],
) -> None:
    backend = MemoryBackend(QUIET)
    ttk = window(backend)
    # summary_buttons holds the images' radios too: the summary's are those of its variable.
    variable = str(ttk.main.summary_format)
    ours = {
        str(b.cget("value")): b
        for b in ttk.main.summary_buttons
        if str(b.cget("variable")) == variable
    }
    assert set(ours) == {"markdown", "markdown_pdf", "pdf"}
    ours["pdf"].invoke()
    assert backend.settings.summary_format == "pdf"
    qt = qt_window(backend)
    assert qt.main.summary_pdf_only.isChecked()  # remembered
    qt.main.summary_md.click()
    assert backend.settings.summary_format == "markdown"
    flet = flet_window(backend)
    assert set(flet.main.summary.radios) == {"markdown", "markdown_pdf", "pdf"}
    flet.main.summary.choose("pdf")
    assert backend.settings.summary_format == "pdf"


def test_ac_07_its_texts_in_both_languages() -> None:
    for language, pdf_only in (("en", "PDF only"), ("es", "Solo PDF")):
        text = (ROOT / "src" / "clearmd" / "i18n" / f"{language}.toml").read_text(encoding="utf-8")
        assert f'summary_pdf_only = "{pdf_only}"' in text  # the choice on step 1
        assert f'summary_pdf = "{pdf_only}"' in text  # the setting
        assert "summary_pdf_only = " in text.split("[cli.help]")[1]  # the command line's help
