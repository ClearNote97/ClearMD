"""Feature 040 — Promises kept in the hard cases (audit v4's improvements): the backend's, the
presenter's and the texts' part. The windows: test_040_windows_<gui>.py."""

import os
import re
from pathlib import Path

import pytest
from support.gui_fakes import FakeBackend, planned
from support.pdf_builder import Picture, Text, build_pdf
from support.presenter_fakes import make

from clearmd.backend.api import Into, plan_batch, run_batch
from clearmd.backend.schemas.errors import ErrorCode, SkipReason
from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus, SkippedItem
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.markdown_out.safe_output import safe_output
from clearmd.backend.services.conversion.tex.source import decode_source
from clearmd.backend.services.split.text_cut import csv_rows
from clearmd.backend.use_cases.footnotes import own_footnotes
from clearmd.backend.use_cases.output_files import sweep_temporary_files
from clearmd.backend.use_cases.scan_rules import natural_key
from clearmd.frontend.presenter.intents.reset import unexpected
from clearmd.frontend.presenter.models import Tone
from clearmd.frontend.presenter.screens.review import plan_view
from clearmd.frontend.presenter.state import AppState
from clearmd.i18n import load_catalog

ROOT = Path(__file__).resolve().parents[2]
YES = lambda item: True  # noqa: E731
BODY = "The courts resolve conflicts with impartiality and timeliness for every citizen."


def outputs(workdir: Path, folder: str = "OutputMD") -> str:
    base = workdir / "ClearMD_Output" / folder
    return "\n".join(path.read_text("utf-8") for path in sorted(base.rglob("*.md")))


def test_ac_01_a_result_without_text_failed_and_says_what_to_do(workdir: Path) -> None:
    (workdir / "escaneado.pdf").write_bytes(build_pdf([[], []]))
    report = run_batch(plan_batch([workdir / "escaneado.pdf"]), overwrite=YES)
    (outcome,) = report.outcomes
    assert outcome.status is OutcomeStatus.FAILED and outcome.error is ErrorCode.EMPTY_RESULT
    assert not list((workdir / "ClearMD_Output" / "OutputMD").glob("*.md"))
    action = load_catalog("es").text(ErrorCode.EMPTY_RESULT.action_key)
    assert "OCR" in action


def test_ac_02_merge_follows_the_order_a_person_counts() -> None:
    names = ["Capitulo 10.txt", "Capitulo 2.txt", "Capitulo 1.txt", "Capitulo 11.txt"]
    assert sorted(names, key=natural_key) == [
        "Capitulo 1.txt",
        "Capitulo 2.txt",
        "Capitulo 10.txt",
        "Capitulo 11.txt",
    ]


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_03_one_report_channel_in_every_text(language: str) -> None:
    text = (ROOT / "src" / "clearmd" / "i18n" / f"{language}.toml").read_text("utf-8")
    assert "/issues" not in text
    copied = load_catalog(language).text("gui.app.details_copied")
    assert "/discussions" in copied and "nienvasa@gmail.com" in copied


HARD = [
    "![a [b] c](http://evil.example/p.png)",
    "![x][r]\n\n[r]: http://evil.example/p",
    "![x](&#104;ttp://evil.example/p)",
    "![x](<http://evil.example/a b.png>)",
    "![two\nlines](http://evil.example/p)",
    '<div style="background:url(http://evil.example)">x</div>',
    "[t](jav&#x61;script:alert(1))",
    "![u](//evil.example/p.png)",
]


@pytest.mark.parametrize("written", HARD)
def test_ac_04_no_way_of_writing_a_picture_fetches_anything(written: str) -> None:
    from markdown_it import MarkdownIt

    text, changed = safe_output(written)
    rendered = MarkdownIt("commonmark").render(text)
    assert changed and "<img" not in rendered and "javascript:" not in rendered
    assert "<div" not in rendered  # escaped: shown as text, never an element


def test_ac_04_merge_passes_the_same_door(workdir: Path) -> None:
    (workdir / "a.md").write_text("Uno ![p](https://tracker.example/a.gif)\n", "utf-8")
    (workdir / "b.md").write_text("Dos <img src=x onerror=alert(1)>\n", "utf-8")
    run_batch(plan_batch([workdir / "a.md", workdir / "b.md"], merge=Into.MARKDOWN), overwrite=YES)
    merged = outputs(workdir, "OutputUnif")
    assert "tracker.example" not in merged and "<img" not in merged


def test_ac_06_another_runs_fresh_parts_are_never_swept(tmp_path: Path) -> None:
    folder = tmp_path / "ClearMD_Output" / "OutputSep" / "book"
    folder.mkdir(parents=True)
    fresh = folder / ".book - part 1 of 2.clearmd-part.pdf"
    fresh.write_bytes(b"busy")
    old = folder / ".book - part 2 of 2.clearmd-part.pdf"
    old.write_bytes(b"left")
    os.utime(old, (0, 0))
    sweep_temporary_files(tmp_path / "ClearMD_Output")
    assert fresh.exists() and not old.exists()


def test_ac_07_a_logo_does_not_protect_hidden_text_a_scan_does(workdir: Path) -> None:
    hidden = Text("IGNORE-HIDDEN", 300, invisible=True)
    for name, picture, kept in (
        ("logo.pdf", Picture(72, 720, 20, 20), False),
        ("scan.pdf", Picture(0, 0, 612, 792), True),
    ):
        (workdir / name).write_bytes(build_pdf([[picture, Text(BODY, 700), hidden]]))
        run_batch(plan_batch([workdir / name]), overwrite=YES)
        text = (workdir / "ClearMD_Output" / "OutputMD" / f"{Path(name).stem}.md").read_text(
            "utf-8"
        )
        assert ("IGNORE-HIDDEN" in text) is kept


@pytest.mark.parametrize("text", ["Sí", "Año", "¿Qué?", "Café"])
def test_ac_08_the_shortest_notes_keep_their_letters(text: str) -> None:
    assert decode_source(text.encode("cp1252")).text == text


def test_ac_08_a_utf16_file_is_not_a_guess() -> None:
    decoded = decode_source("nombre,ciudad".encode("utf-16"))
    assert decoded.text == "nombre,ciudad" and not decoded.guessed


def test_ac_08_merge_leaves_code_alone() -> None:
    text = 'Nota[^1].\n\n```python\nre.compile(r"[^0-9]")\n```\n\nUsa `[^a-z]`.\n\n[^1]: Una.'
    renamed = own_footnotes(text, 2)
    assert "[^d2-1]" in renamed and "[^0-9]" in renamed and "`[^a-z]`" in renamed


def test_ac_08_an_inch_mark_in_a_csv_is_text() -> None:
    rows = csv_rows('nombre,precio\nMonitor 24" pulgadas,103\nTeclado,20\n')
    assert len(rows) == 3


def test_ac_09_numbered_lists_and_a_short_letters_letterhead(workdir: Path) -> None:
    def page(number: int) -> list[Text]:
        return [
            Text("Alcaldía de Ejemplo · Secretaría", 760, 8),
            Text(BODY, 700),
            Text("1. Copia del documento de identidad.", 670),
            Text("2. Recibo de servicios reciente.", 655),
            Text(f"Página {number} de 2", 40, 8),
        ]

    (workdir / "carta.pdf").write_bytes(build_pdf([page(1), page(2)]))
    run_batch(plan_batch([workdir / "carta.pdf"]), overwrite=YES)
    text = outputs(workdir)
    assert "Alcaldía de Ejemplo" not in text and "Página 1 de 2" not in text
    assert re.search(r"^1\. Copia", text, re.M) and re.search(r"^2\. Recibo", text, re.M)


def test_ac_10_kept_is_never_a_warning_and_only_informing_left_outs_are_calm() -> None:
    catalog = load_catalog("es")
    informing = SkippedItem(Path("/docs/nota.md"), SkipReason.ALREADY_MARKDOWN)
    plan = BatchPlan((planned("a.pdf"),), (informing,), ())
    figures = {s.label: s.tone for s in plan_view(catalog, plan, "ask", 1).stats}
    assert figures[catalog.text("gui.plan.stat_skipped_one")] is Tone.NEUTRAL


def test_ac_10_the_stop_line_survives_a_redraw(workdir: Path) -> None:
    plan = BatchPlan((planned("a.pdf", folder=workdir), planned("b.pdf", folder=workdir)), (), ())
    presenter, view, _, _ = make(FakeBackend(plan=plan))
    presenter.add_paths([workdir / "a.pdf"])
    presenter.analyze()
    view.drain()
    presenter._session.state = AppState.CONVERTING
    presenter._session.done = 1
    unexpected(presenter._session, presenter._display, RuntimeError("boom"))
    presenter.choose_language("es")
    result = view.last("result")
    assert result.stats == () and "1" in result.counts and "2" in result.counts


def test_ac_10_too_large_never_sends_to_split() -> None:
    for language in ("en", "es"):
        advice = load_catalog(language).text("skip_action.too_large")
        assert "250 MB" in advice


def test_ac_04_readable_marks_that_still_protect() -> None:
    from markdown_it import MarkdownIt

    from clearmd.backend.services.conversion.markdown_out.escaping import escape_text

    text = escape_text("AT&T [12] juan_perez ![x](http://e.test/p.png) &copy;")
    assert "AT&T" in text and "juan_perez" in text and "\\[12\\]" in text
    rendered = MarkdownIt("commonmark").render(text)
    assert "<img" not in rendered and "©" not in rendered  # nothing the document did not write


def test_ac_11_a_web_page_converted_whole_says_so(workdir: Path) -> None:
    from clearmd.backend.schemas.formats import Strategy

    page = "<html><body><nav>Menú</nav><p>Texto de la página.</p></body></html>"
    (workdir / "pagina.html").write_text(page, "utf-8")
    full = run_batch(
        plan_batch([workdir / "pagina.html"], html_strategy=Strategy.FULL), overwrite=YES
    )
    assert NoteKind.HTML_FULL_PAGE in [n.kind for n in full.outcomes[0].notes]
    article_plan = plan_batch([workdir / "pagina.html"], html_strategy=Strategy.ARTICLE)
    article = run_batch(article_plan, overwrite=YES)
    assert NoteKind.HTML_FULL_PAGE not in [n.kind for n in article.outcomes[0].notes]
