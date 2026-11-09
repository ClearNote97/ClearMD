"""Feature 036 — Clear messages, a kind first run, progress and estimates
(spec/features/036_*/spec.md): the backend, the presenter and the texts. The installer:
test_036_installer.py."""

import os
import re
import threading
import time
from collections.abc import Callable
from dataclasses import replace
from multiprocessing import Pipe
from pathlib import Path
from typing import Any

import pytest

from clearmd.backend.api import Cut, Keep, SplitSpec, plan_batch, run_batch
from clearmd.backend.schemas.errors import ConversionError, ErrorCode, SkipReason
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.models import OutcomeStatus
from clearmd.backend.services.worker.processes import wait_for_response
from clearmd.backend.services.worker.protocol import Detected, Progress
from clearmd.backend.use_cases.cancel import CancelToken
from clearmd.backend.use_cases.splitting import split_cost, split_memory
from clearmd.frontend.presenter.intents.reset import unexpected
from clearmd.frontend.presenter.screens.convert import progress_view
from clearmd.i18n import load_catalog

YES = lambda item: True  # noqa: E731
WINDOW_FORBIDDEN = re.compile(r"--[a-z]|markitdown|openpyxl|pdfium|\bCLI\b|zip bomb|bomba ZIP")


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_01_window_texts_carry_no_command_line_and_no_library(language: str) -> None:
    catalog = load_catalog(language)
    window = [
        key
        for key in catalog.keys()
        if key.startswith(("skip.", "skip_action.", "error.", "gui.", "note.", "summary."))
    ]
    offending = {key: catalog.text_template(key) for key in window}
    offending = {k: v for k, v in offending.items() if WINDOW_FORBIDDEN.search(v)}
    assert offending == {}


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_01_the_terminal_speaks_its_options(language: str) -> None:
    window, terminal = load_catalog(language), load_catalog(language).for_terminal()
    for key in ("skip_action.existing_output", "skip_action.cut_not_for_markdown"):
        assert "--" in terminal.text(key) and "--" not in window.text(key)


def test_ac_02_an_encrypted_word_file_is_told_as_protected(workdir: Path) -> None:
    (workdir / "secret.docx").write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\0" * 2048)
    report = run_batch(plan_batch([workdir / "secret.docx"]), overwrite=YES)
    if report.outcomes:  # detected as a Word file by its name: it reaches the converter
        assert report.outcomes[0].error is ErrorCode.PASSWORD_PROTECTED
    else:
        assert report.skipped


@pytest.mark.parametrize("cut", [Cut.PARTS, Cut.WORDS])
@pytest.mark.parametrize("name", ["empty.txt", "empty.md"])
def test_ac_02_an_empty_file_is_empty_not_scanned(workdir: Path, cut: Cut, name: str) -> None:
    (workdir / name).write_text("\n", "utf-8")
    spec = SplitSpec(cut, 2 if cut is Cut.PARTS else 500, Keep.MARKDOWN)
    report = run_batch(plan_batch([workdir / name], split=spec), overwrite=YES)
    assert report.outcomes[0].error is ErrorCode.EMPTY_FILE


def test_ac_03_old_office_files_and_pictures_say_what_to_do(workdir: Path) -> None:
    for name in ("old.doc", "sheet.xls", "deck.ppt", "photo.jpg"):
        (workdir / name).write_bytes(b"\xd0\xcf\x11\xe0 not much")
    plan = plan_batch([workdir])
    reasons = {item.path.name: item.reason for item in plan.skipped}
    assert (
        reasons["old.doc"] is reasons["sheet.xls"] is reasons["deck.ppt"] is SkipReason.OLD_OFFICE
    )
    assert reasons["photo.jpg"] is SkipReason.IMAGE
    catalog = load_catalog("es")
    assert ".docx" in catalog.text("skip_action.old_office")


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_04_the_unexpected_error_hides_the_detail_behind_copy_details(language: str) -> None:
    from support.presenter_fakes import make

    presenter, view, _, _ = make()
    presenter.save_settings(replace(presenter.settings, language=language))
    view.drain()
    catalog = load_catalog(language)
    error = FileNotFoundError(
        r"C:\Users\María Pérez\Documentos\Despido.pdf is gone; /home/x/a.docx"
    )
    unexpected(presenter._session, presenter._display, error)
    message = view.last("message")
    assert "FileNotFoundError" not in message and "github.com/ClearNote97/ClearMD/issues" in message
    assert view.last("details_button") == catalog.text("gui.app.copy_details")
    presenter.copy_details()
    copied = view.last("copied")
    placeholder = catalog.text("gui.app.file_placeholder")
    assert f"<{placeholder}>.pdf" in copied and f"<{placeholder}>.docx" in copied
    assert "María" not in copied and "/home/x" not in copied and "FileNotFoundError" in copied
    assert view.last("message") == catalog.text("gui.app.details_copied")
    assert view.last("details_button") is None


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_04_the_terminal_says_where_to_tell(language: str) -> None:
    text = (
        load_catalog(language).for_terminal().text("cli.unexpected_error", detail="KeyError: 'x'")
    )
    assert "github.com/ClearNote97/ClearMD/issues" in text and "KeyError" in text


class _Alive:
    """A stand-in for the worker process: alive, this test's own memory."""

    pid = os.getpid()

    def is_alive(self) -> bool:
        return True


def _answer_after(send: Callable[[Any], None], beats: int, every: float) -> threading.Thread:
    def run() -> None:
        for done in range(1, beats + 1):
            time.sleep(every)
            send(Progress(done, beats))
        send(Detected(None))

    thread = threading.Thread(target=run)
    thread.start()
    return thread


def _wait(limits: Limits, beats: int, every: float, heard: list[tuple[int, int]]) -> object:
    ours, theirs = Pipe()
    cancel = CancelToken()
    cancel.on_progress(lambda done, total: heard.append((done, total)))
    thread = _answer_after(theirs.send, beats, every)
    try:
        crashed = lambda process: ConversionError(ErrorCode.WORKER_CRASHED)  # noqa: E731
        return wait_for_response(ours, _Alive(), cancel, limits, lambda: None, crashed)  # type: ignore[arg-type]
    finally:
        thread.join()


def test_ac_05_a_file_that_keeps_moving_is_not_stopped() -> None:
    heard: list[tuple[int, int]] = []
    limits = Limits(time_per_file=0.6)
    answer = _wait(limits, beats=6, every=0.3, heard=heard)  # 1.8 s in all, never 0.6 s still
    assert isinstance(answer, Detected) and heard[-1] == (6, 6)


def test_ac_05_a_file_that_stops_moving_is_stopped() -> None:
    limits = Limits(time_per_file=0.3)
    with pytest.raises(ConversionError) as stopped:
        _wait(limits, beats=1, every=0.8, heard=[])
    assert stopped.value.code is ErrorCode.TIMED_OUT


def test_ac_05_the_window_says_page_n_of_m() -> None:
    catalog = load_catalog("en")
    view = progress_view(catalog, (1, 1, "big.pdf", None, "pdf"), 0, 30.0, (40, 120))
    assert view.long_file == catalog.text("gui.progress.pages", done="40", total="120")


def test_ac_05_a_real_pdf_reports_its_pages(workdir: Path) -> None:
    from support.pdf_builder import Text, build_pdf

    (workdir / "book.pdf").write_bytes(build_pdf([[Text(f"Page {n}", 700)] for n in range(1, 4)]))
    events: list[object] = []
    report = run_batch(plan_batch([workdir / "book.pdf"]), overwrite=YES, on_event=events.append)
    assert report.outcomes[0].status is OutcomeStatus.CONVERTED
    pages = [e for e in events if type(e).__name__ == "ConversionProgress"]
    assert pages and pages[-1].done == pages[-1].pages == 3  # type: ignore[attr-defined]


def test_ac_06_splitting_excel_costs_what_excel_costs() -> None:
    limits = Limits()
    spec = SplitSpec(Cut.PARTS, 4, Keep.PDF)
    size = 10 * 1024**2
    excel = split_cost(limits, size, spec, FormatId.XLSX)
    assert excel >= 4 * limits.estimated_seconds(FormatId.XLSX, size)  # one load per part
    assert split_memory(limits, FormatId.XLSX, 2 * 1024**3) is not None
    assert split_memory(limits, FormatId.TXT, 2 * 1024**3) is None


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_08_texts(language: str) -> None:
    catalog = load_catalog(language)
    for key in ("error.empty_file.message", "skip.old_office", "skip.image", "gui.progress.pages"):
        assert catalog.text_template(key)
