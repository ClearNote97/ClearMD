"""Feature 038 — Say only what is true, and start faster (spec/features/038_*/spec.md): the
backend, the presenter, the texts and the start-up. The windows: test_038_windows_<gui>.py."""

import re
import subprocess
import sys
from pathlib import Path

import pytest
from support.gui_fakes import FakeBackend, planned
from support.pdf_builder import Text, build_pdf
from support.presenter_fakes import make

from clearmd.backend.api import Cut, Into, Keep, SplitSpec, plan_batch, run_batch, without_paths
from clearmd.backend.schemas.errors import ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus
from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.pdf.blocks.equation_latex import incoherent
from clearmd.backend.services.conversion.pdf.tables.build import joined_continuations
from clearmd.backend.services.split.text_cut import balanced_cuts
from clearmd.frontend.cli import main
from clearmd.frontend.presenter.chrome.header import header_of
from clearmd.frontend.presenter.intents.reset import unexpected
from clearmd.frontend.presenter.state import AppState
from clearmd.i18n import load_catalog

YES = lambda item: True  # noqa: E731
ROOT = Path(__file__).resolve().parents[2]
SPANISH = "El año pasado los señores Núñez y Peña firmaron el acta.\n" * 3


def outputs(workdir: Path, folder: str = "OutputMD") -> str:
    base = workdir / "ClearMD_Output" / folder
    return "\n".join(path.read_text("utf-8") for path in sorted(base.rglob("*.md")))


def test_ac_01_a_windows_text_keeps_its_letters_in_every_tool(workdir: Path) -> None:
    (workdir / "acta.txt").write_bytes(SPANISH.encode("cp1252"))
    (workdir / "lista.csv").write_bytes("nombre;ciudad\nNúñez;Peña\n".encode("cp1252"))
    report = run_batch(plan_batch([workdir / "acta.txt", workdir / "lista.csv"]), overwrite=YES)
    text = outputs(workdir)
    assert "año" in text and "Núñez" in text and "ń" not in text
    assert "| Núñez | Peña |" in text
    notes = [note.kind for outcome in report.outcomes for note in outcome.notes]
    assert NoteKind.ENCODING_GUESSED in notes
    merged = plan_batch([workdir / "acta.txt", workdir / "lista.csv"], merge=Into.MARKDOWN)
    run_batch(merged, overwrite=YES)
    assert "señores" in outputs(workdir, "OutputUnif")


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_01_the_guess_is_told_in_plain_words(language: str) -> None:
    text = load_catalog(language).text_template("note.encoding_guessed").lower()
    assert "codificación" not in text and "encoding" not in text


@pytest.mark.parametrize(
    ("detail", "leak"),
    [
        ("KeyError: 'Historia clinica Ana.pdf'", "Historia"),
        (r"OSError: D:\Clientes\Ana Ruiz\ClearMD_Output is locked", "Ruiz"),
        ("ValueError: bad cell in Informe Pérez", "Pérez"),
    ],
)
def test_ac_02_copy_details_hides_names(detail: str, leak: str) -> None:
    hidden = without_paths(detail, "file", ["Informe Pérez.docx", "Informe Pérez"])
    assert leak not in hidden and "<file>" in hidden


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_02_the_texts_promise_less_and_say_how_to_report(language: str) -> None:
    catalog = load_catalog(language)
    how = catalog.text("report.how")
    for key in ("gui.app.unexpected_error", "error.conversion_failed.action"):
        assert how in catalog.text(key)
    copied = catalog.text("gui.app.details_copied").lower()
    assert "tried" in copied or "intentamos" in copied
    everything = " ".join(catalog.text_template(k) for k in catalog.keys())
    assert "attach the summary" not in everything and "adjunta el resumen" not in everything


def test_ac_03_n_parts_even_with_the_weight_at_the_end(workdir: Path) -> None:
    assert len(balanced_cuts([5, 5, 10000], 3)) == 2
    assert len(balanced_cuts([10000, 5, 5], 3)) == 2
    body = "# One\n\nshort\n\n# Two\n\nshort\n\n# Three\n\n" + "\n\n".join(["word " * 60] * 25)
    (workdir / "libro.md").write_text(body, "utf-8")
    run_batch(plan_batch([workdir / "libro.md"], split=SplitSpec(Cut.PARTS, 3)), overwrite=YES)
    assert len(list((workdir / "ClearMD_Output" / "OutputSep" / "libro").glob("*.md"))) == 3


def test_ac_03_fewer_parts_than_asked_are_told(workdir: Path) -> None:
    (workdir / "two.pdf").write_bytes(build_pdf([[Text("One", 700)], [Text("Two", 700)]]))
    report = run_batch(
        plan_batch([workdir / "two.pdf"], split=SplitSpec(Cut.PARTS, 5, Keep.PDF)), overwrite=YES
    )
    (outcome,) = report.outcomes
    assert outcome.parts == 2 and NoteKind.PARTS_FEWER in [n.kind for n in outcome.notes]


def test_ac_04_an_error_during_a_task_lands_on_results(workdir: Path) -> None:
    root = workdir / "ClearMD_Output"
    root.mkdir()
    plan = BatchPlan((planned("a.pdf", folder=workdir),), (), ())
    presenter, view, _, _ = make(FakeBackend(plan=plan))
    presenter.add_paths([workdir / "a.pdf"])
    presenter.analyze()
    view.drain()
    presenter._session.state = AppState.CONVERTING  # an error while the task runs
    unexpected(presenter._session, presenter._display, RuntimeError("boom"))
    view.drain()
    assert presenter.page == 4 and presenter.state is AppState.FINISHED_WITH_PROBLEMS
    assert view.last("result").folders == (root,)
    assert str(root) in view.last("result").where  # the folder, written
    assert view.last("details_button")


def test_ac_05_a_wrapped_cell_and_an_incoherent_formula() -> None:
    rows = [["Year", "Name"], ["2020", "A long name"], ["", "that goes on"], ["2021", "B"]]
    assert joined_continuations(rows) == [
        ["Year", "Name"],
        ["2020", "A long name that goes on"],
        ["2021", "B"],
    ]
    assert incoherent(r"\underset{o}{\frac{EF_{o}^{t}(x)}{1}}") and incoherent("EF^{t+}")
    assert not incoherent(r"\frac{x}{1+y}") and not incoherent("x^{2}+y_{i}")


def test_ac_07_split_advice_only_for_formats_split_takes(workdir: Path) -> None:
    from clearmd.backend.api import error_text
    from clearmd.backend.schemas.models import ConversionOutcome

    catalog = load_catalog("en")
    for name, splittable in (("a.pdf", True), ("a.docx", False)):
        outcome = ConversionOutcome(planned(name), OutcomeStatus.STOPPED, ErrorCode.TIMED_OUT)
        said = error_text(catalog, outcome)
        assert ("Split" in said) is splittable and ("PDF" in said) is not splittable or splittable


def test_ac_07_an_empty_file_is_empty_in_every_tool(workdir: Path) -> None:
    for name in ("empty.pdf", "empty.docx", "empty.txt"):
        (workdir / name).write_bytes(b"")
    report = run_batch(plan_batch([workdir]), overwrite=YES)
    assert {o.item.source.name: o.error for o in report.outcomes} == dict.fromkeys(
        ("empty.docx", "empty.pdf", "empty.txt"), ErrorCode.EMPTY_FILE
    )


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_07_step_3_and_the_hints_tell_the_truth(language: str) -> None:
    from clearmd.frontend.presenter.models import StateView

    catalog = load_catalog(language)
    working = header_of(catalog, StateView(AppState.CONVERTING, "", frozenset(), 3, 3), None)
    assert working.subtitle == catalog.text("gui.page.convert_subtitle_working")
    assert catalog.text("gui.result.again") in catalog.text(
        "gui.nav.done", more=catalog.text("gui.result.again")
    )
    everything = " ".join(catalog.text_template(k) for k in catalog.keys())
    assert "(s)" not in everything
    assert not re.search(
        r"\b(batch|lote)\b",
        " ".join(
            catalog.text_template(k) for k in catalog.keys() if k.startswith(("gui.", "summary."))
        ),
    )


def test_ac_07_the_command_line_refuses_a_merge_of_one(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (workdir / "a.txt").write_text("a\n", "utf-8")
    assert main([str(workdir / "a.txt"), "--merge", "markdown"]) == 2
    assert load_catalog("en").text("cli.merge_needs_two") in capsys.readouterr().err


def test_ac_08_parts_in_the_other_language_are_recognised(workdir: Path) -> None:
    (workdir / "doc.md").write_text("# A\n\na\n\n# B\n\nb\n\n# C\n\nc\n", "utf-8")
    spec = SplitSpec(Cut.PARTS, 3)
    run_batch(plan_batch([workdir / "doc.md"], split=spec), overwrite=YES, language="en")
    run_batch(
        plan_batch([workdir / "doc.md"], split=SplitSpec(Cut.PARTS, 2)),
        overwrite=YES,
        language="es",
    )
    names = sorted(p.name for p in (workdir / "ClearMD_Output" / "OutputSep" / "doc").iterdir())
    assert names == ["doc - parte 1 de 2.md", "doc - parte 2 de 2.md"]


def test_ac_08_images_only_in_convert(workdir: Path) -> None:
    (workdir / "a.md").write_text("a\n", "utf-8")
    (workdir / "b.md").write_text("b\n", "utf-8")
    plan = plan_batch([workdir / "a.md", workdir / "b.md"], merge=Into.MARKDOWN)
    report = run_batch(plan, overwrite=YES, images=True)
    assert all(not outcome.item.images for outcome in report.outcomes)


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_08_the_names_match_the_catalogs(language: str) -> None:
    from clearmd.backend.schemas.formats import IMAGE_SUFFIXES, PART_NAMES

    catalog = load_catalog(language)
    assert catalog.text("images.suffix") in IMAGE_SUFFIXES
    assert catalog.text_template("split.part_name") in PART_NAMES


@pytest.mark.parametrize(
    "entry",
    [
        "clearmd.frontend.cli.app",
        "clearmd.frontend.ttk.app",
        "clearmd.frontend.pyside.app",
        "clearmd.frontend.flet.app",
    ],
)
def test_ac_09_no_interface_loads_the_converters_at_start(entry: str) -> None:
    heavy = "('pypdfium2', 'openpyxl', 'lxml')"
    code = f"import sys, {entry}; print([m for m in {heavy} if m in sys.modules])"
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "[]"


def test_ac_09_ci_and_the_installer_are_set_for_speed() -> None:
    conftest = (ROOT / "tests" / "conftest.py").read_text("utf-8")
    assert "_WINDOW_TESTS" in conftest
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text("utf-8")
    assert "--durations=15" in ci and "if: always()" in ci
    spec = (ROOT / "packaging" / "clearmd.spec").read_text("utf-8")
    assert 'name="ClearMD-Classic"' in spec
    iss = (ROOT / "packaging" / "installer" / "clearmd.iss").read_text("utf-8-sig")
    assert 'dist\\ClearMD-Classic\\*"; DestDir: "{app}"' in iss
    assert "opened and closed in" in (ROOT / "packaging" / "check_executables.sh").read_text(
        "utf-8"
    )


def test_ac_10_pdf_estimates_follow_real_documents() -> None:
    limits = Limits()
    assert limits.estimated_seconds(FormatId.PDF, 1024**2) <= 5
    assert limits.estimated_memory(FormatId.PDF, 200 * 1024**2) < limits.worker_memory


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_10_texts(language: str) -> None:
    catalog = load_catalog(language)
    for key in ("gui.close.title", "gui.close.keep", "cli.merge_needs_two", "note.parts_fewer"):
        assert catalog.text_template(key)
