"""Feature 039, the backend's part: audit v3's improvements on what a result holds and says.
The presenter and the texts: test_039_presenter_and_texts.py; the windows: test_039_windows_*."""

import zipfile
from pathlib import Path

import pytest
from support.pdf_builder import Text, build_pdf

from clearmd.backend.api import Cut, Into, Keep, SplitSpec, plan_batch, run_batch
from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.models import OutcomeStatus
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.markdown_out.safe_output import safe_output
from clearmd.backend.services.conversion.tex.source import decode_source
from clearmd.backend.use_cases import split_notes

YES = lambda item: True  # noqa: E731
BODY = "The courts resolve conflicts with impartiality and timeliness for every citizen."


def outputs(workdir: Path, folder: str = "OutputMD") -> str:
    base = workdir / "ClearMD_Output" / folder
    return "\n".join(path.read_text("utf-8") for path in sorted(base.rglob("*.md")))


def notes_of(report: object) -> list[NoteKind]:
    return [note.kind for outcome in report.outcomes for note in outcome.notes]  # type: ignore[attr-defined]


# The hard cases: one short line each, as Windows saves them (C-1: a long one passed by luck).
SHORT = [
    ("Canción de cuna, mañana español árbol corazón", "es"),
    ("José;Bogotá;Medellín", "es"),
    ("He said “that’s fine” — €5", "en"),
    ("Ça m’a plu, très élégant", "fr"),
]


@pytest.mark.parametrize(("text", "language"), SHORT)
def test_ac_01_a_short_windows_text_keeps_its_letters(text: str, language: str) -> None:
    decoded = decode_source(text.encode("cp1252"))
    assert decoded.text == text and decoded.encoding == "cp1252"


def test_ac_01_another_script_is_still_detected() -> None:
    russian = "Привет, как дела у тебя сегодня"
    assert decode_source(russian.encode("cp1251")).text == russian


def test_ac_01_a_short_csv_converts_with_its_letters(workdir: Path) -> None:
    (workdir / "ciudades.csv").write_bytes("nombre;ciudad\r\nJosé;Bogotá\r\n".encode("cp1252"))
    report = run_batch(plan_batch([workdir / "ciudades.csv"]), overwrite=YES)
    assert "| José | Bogotá |" in outputs(workdir)
    assert NoteKind.ENCODING_GUESSED in notes_of(report)


HOSTILE = [
    ("![p](https://tracker.example/open.gif?u=1)", "[image: p]"),
    ("![s](\\\\host\\share\\a.png)", "[image: s]"),
    ("[t](javascript:alert(1))", "t"),
    ("[f](file://///host/share/x)", "f"),
    ("<img src=x onerror=alert(1)>", "&lt;img"),
]


@pytest.mark.parametrize(("written", "safe"), HOSTILE)
def test_ac_02_nothing_in_a_result_fetches_or_runs(written: str, safe: str) -> None:
    text, changed = safe_output(f"Before {written} after")
    assert safe in text and changed == 1


@pytest.mark.parametrize(
    "kept", ["![i](Doc_imagenes/i1.png)", "[w](https://example.org/a_(b))", "`![a](http://x)`"]
)
def test_ac_02_own_images_web_links_and_code_stay(kept: str) -> None:
    assert safe_output(kept) == (kept, 0)


def test_ac_02_an_email_page_converts_in_memory_and_safely(workdir: Path) -> None:
    body = '<p>Hola</p><img src="https://tracker.example/p.gif"><p>Texto del correo.</p>'
    mail = f"Subject: Prueba\nFrom: a@b.c\nContent-Type: text/html; charset=utf-8\n\n{body}\n"
    (workdir / "correo.eml").write_text(mail, encoding="utf-8")
    run_batch(plan_batch([workdir / "correo.eml"]), overwrite=YES)
    text = outputs(workdir)
    assert "Texto del correo." in text and "tracker.example" not in text


def test_ac_02_the_summary_never_shows_a_persons_folder(workdir: Path) -> None:
    from clearmd.backend.api import without_paths

    detail = "PermissionError: [Errno 13] Permission denied: '/home/ana.ruiz/Informes/acta.txt'"
    hidden = without_paths(detail, "file")
    assert "ana.ruiz" not in hidden and "<file>.txt" in hidden
    assert without_paths("ValueError: <script>x</script>", "file").endswith("</script>")


def _pdf(workdir: Path, name: str, pages: int) -> Path:
    path = workdir / name
    path.write_bytes(build_pdf([[Text(f"{BODY} Page {n}.", 700)] for n in range(pages)]))
    return path


def test_ac_06_one_stopped_part_never_costs_the_others(
    workdir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _pdf(workdir, "informe.pdf", 3)
    real = split_notes.part_markdown
    calls = {"n": 0}

    def second_stops(runner, part, cancel):  # type: ignore[no-untyped-def]
        calls["n"] += 1
        return None if calls["n"] == 2 else real(runner, part, cancel)

    monkeypatch.setattr("clearmd.backend.use_cases.splitting.part_markdown", second_stops)
    spec = SplitSpec(Cut.PARTS, 3, Keep.MARKDOWN)
    report = run_batch(plan_batch([source], split=spec), overwrite=YES)
    (outcome,) = report.outcomes
    assert outcome.status is OutcomeStatus.CONVERTED
    folder = outcome.item.target
    assert len(list(folder.glob("*.md"))) == 2 and len(list(folder.glob("*.pdf"))) == 1
    assert NoteKind.PARTS_NOT_CONVERTED in notes_of(report)


def test_ac_06_a_part_that_stops_is_none_not_an_error() -> None:
    class Stops:
        def convert(self, item: object, cancel: object) -> object:
            raise ConversionError(ErrorCode.TIMED_OUT, "stopped")

    assert split_notes.part_markdown(Stops(), None, None) is None  # type: ignore[arg-type]


def test_ac_06_an_empty_folder_is_not_a_result(workdir: Path) -> None:
    source = _pdf(workdir, "acta.pdf", 2)
    spec = SplitSpec(Cut.PARTS, 2, Keep.MARKDOWN)
    plan = plan_batch([source], split=spec)
    (item,) = plan.conversions
    item.target.mkdir(parents=True)  # left behind by an earlier failure
    again = plan_batch([source], split=spec)
    assert not again.conversions[0].exists


def test_ac_08_text_no_one_sees_is_left_out_and_said(workdir: Path) -> None:
    page = [
        Text(BODY, 700),
        Text("IGNORE-OFFPAGE", 2000),
        Text("IGNORE-TINY", 400, size=0.5),
        Text("IGNORE-INVISIBLE", 300, invisible=True),
    ]
    (workdir / "oculto.pdf").write_bytes(build_pdf([page]))
    report = run_batch(plan_batch([workdir / "oculto.pdf"]), overwrite=YES)
    text = outputs(workdir)
    assert "courts" in text and "IGNORE" not in text
    assert NoteKind.PDF_HIDDEN_TEXT_LEFT_OUT in notes_of(report)


def test_ac_08_word_tables_with_merged_cells_are_told(workdir: Path) -> None:
    from clearmd.backend.services.conversion.markitdown_adapter import merged_cells

    path = workdir / "tabla.docx"
    with zipfile.ZipFile(path, "w") as package:
        package.writestr(
            "word/document.xml", '<w:tc><w:tcPr><w:gridSpan w:val="2"/></w:tcPr></w:tc>'
        )
    assert merged_cells(path)


def test_ac_08_merge_keeps_each_documents_notes_and_footnotes(workdir: Path) -> None:
    (workdir / "a.txt").write_bytes("Canción de cuna, mañana.".encode("cp1252"))
    (workdir / "b.md").write_text("Texto[^1].\n\n[^1]: Nota de b.\n", encoding="utf-8")
    (workdir / "c.md").write_text("Otro[^1].\n\n[^1]: Nota de c.\n", encoding="utf-8")
    plan = plan_batch([workdir / "a.txt", workdir / "b.md", workdir / "c.md"], merge=Into.MARKDOWN)
    report = run_batch(plan, overwrite=YES)
    assert NoteKind.ENCODING_GUESSED in notes_of(report)
    merged = outputs(workdir, "OutputUnif")
    assert "[^d2-1]" in merged and "[^d3-1]" in merged and "[^1]" not in merged


def test_ac_11_web_pages_convert_their_article_by_default() -> None:
    from clearmd.backend.schemas.settings import Settings

    assert Settings().html_strategy == "article"
