"""Feature 035 — Honest signals, a Help that guides, the path (spec/features/035_*/spec.md): the
summary, the presenter and the texts. The windows: test_035_windows_<gui>.py."""

from pathlib import Path

import pytest
from support.gui_fakes import FakeBackend, planned
from support.pdf_builder import Text, build_pdf
from support.presenter_fakes import converted

from clearmd.backend.api import plan_batch, run_batch
from clearmd.backend.schemas.models import BatchPlan, ConversionOutcome, OutcomeStatus
from clearmd.backend.schemas.notes import ConversionNote, NoteKind
from clearmd.frontend.presenter.chrome.secondary import ready_line
from clearmd.frontend.presenter.models import PlanRow, PlanView, RowKind, Stat, Tone
from clearmd.frontend.presenter.screens.help import help_sections
from clearmd.frontend.presenter.state import Tool
from clearmd.i18n import load_catalog

YES = lambda item: True  # noqa: E731


def summary(workdir: Path) -> str:
    return (workdir / "ClearMD_Output" / "Resumen_ClearMD.md").read_text("utf-8")


def test_ac_01_what_clearmd_tidied_is_not_a_problem(workdir: Path) -> None:
    pages = [[Text("Running head", 780), Text(f"Body of page {n}", 600)] for n in range(1, 5)]
    (workdir / "clean.pdf").write_bytes(build_pdf(pages))
    report = run_batch(plan_batch([workdir / "clean.pdf"]), overwrite=YES)
    (outcome,) = report.outcomes
    assert outcome.status is OutcomeStatus.CONVERTED
    assert outcome.notes and not outcome.worth_a_look  # a running head removed: good news
    text = summary(workdir)
    assert text.startswith("# ") and "✅" in text.splitlines()[2]
    catalog = load_catalog("en")
    assert f"## {catalog.text('summary.cleaned')}" in text
    assert f"## {catalog.text('summary.attention')}" not in text


def test_ac_01_a_note_worth_a_look_still_is() -> None:
    item = planned("a.pdf")
    tidy = ConversionNote(NoteKind.PDF_RUNNING_REMOVED)
    look = ConversionNote(NoteKind.PDF_PAGES_WITHOUT_TEXT)
    assert not ConversionOutcome(item, OutcomeStatus.CONVERTED, notes=(tidy,)).worth_a_look
    assert ConversionOutcome(item, OutcomeStatus.CONVERTED, notes=(tidy, look)).worth_a_look


def test_ac_02_kept_is_a_choice_not_a_problem() -> None:
    plan = BatchPlan((planned("a.pdf", exists=True), planned("b.pdf")), (), ())
    _, view, _, _ = converted(FakeBackend(plan=plan))
    result = view.last("result")
    catalog = load_catalog("en")
    assert [row.name for row in result.rows] == []  # kept is not "what needs your attention"
    figures = {stat.label: stat.value for stat in result.stats}
    assert figures[catalog.text("gui.result.stat_kept")] == 1
    assert figures[catalog.text("gui.result.stat_skipped")] == 0
    assert "1 kept" in result.counts and result.folders  # its folder can be opened


def test_ac_02_only_kept_still_opens_the_folder() -> None:
    plan = BatchPlan((planned("a.pdf", exists=True),), (), ())
    _, view, _, _ = converted(FakeBackend(plan=plan))
    assert view.last("result").folders == (Path("/docs/ClearMD_Output"),)
    assert view.last("state").primary.enabled


def test_ac_03_each_row_says_its_kind_and_has_its_tone() -> None:
    fake = FakeBackend(
        plan=BatchPlan((planned("a.pdf"), planned("b.pdf")), (), ()),
        statuses={"a.pdf": OutcomeStatus.FAILED, "b.pdf": OutcomeStatus.STOPPED},
    )
    _, view, _, _ = converted(fake)
    catalog = load_catalog("en")
    rows = {row.name: row for row in view.last("result").rows}
    assert rows["a.pdf"].detail.startswith(catalog.text("gui.result.word_failed"))
    assert rows["b.pdf"].detail.startswith(catalog.text("gui.result.word_stopped"))
    assert {row.tone for row in rows.values()} == {Tone.DANGER}


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize("drops", [True, False])
def test_ac_04_help_describes_the_real_product(language: str, drops: bool) -> None:
    catalog = load_catalog(language)
    sections = dict(help_sections(catalog, drops=drops))
    text = "\n".join(sections.values())
    for tool in Tool:  # every tool of Home, by its button's real name
        assert catalog.for_tool(tool).text("gui.main.convert") in text
    assert catalog.text("gui.nav.next") in text
    assert (catalog.text("gui.help.how_drop") in text) is drops
    assert catalog.text("gui.help.markdown_title") in sections
    assert ".doc" in text and "OutputSep" in text and "OutputUnif" in text


def test_ac_06_results_say_where_the_files_are() -> None:
    _, view, _, _ = converted()
    where = view.last("result").where
    assert where.startswith(load_catalog("en").text_template("gui.result.where.one").split("\n")[0])
    assert str(Path("/docs/ClearMD_Output/OutputMD")) in where


def _plan(existing: int, new: int) -> PlanView:
    rows = [PlanRow(RowKind.EXISTS, f"e{i}", "", "", "pdf") for i in range(existing)]
    rows += [PlanRow(RowKind.CONVERT, f"n{i}", "", "", "pdf") for i in range(new)]
    return PlanView("", tuple(rows), True, (Stat("x", existing + new, Tone.ACCENT),))


@pytest.mark.parametrize(
    ("setting", "answer", "count", "key"),
    [
        ("ask", "keep", 1, "existing_keep"),
        ("ask", True, 3, "existing_replace"),
        ("changed", None, 1, "existing_changed"),
        ("ask", None, 1, "existing_ask"),
    ],
)
def test_ac_08_step_3_tells_what_will_really_be_written(
    setting: str, answer: object, count: int, key: str
) -> None:
    catalog = load_catalog("en")
    line = ready_line(catalog, _plan(2, 1), setting, answer)  # type: ignore[arg-type]
    assert line == "\n".join(
        [catalog.text("gui.convert.ready", count=count), catalog.plural(f"gui.convert.{key}", 2)]
    )


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_08_the_welcome_counts_no_steps(language: str) -> None:
    intro = load_catalog(language).text("gui.welcome.intro").lower()
    assert not any(word in intro for word in ("three", "tres", "four", "cuatro"))


def test_ac_08_no_where_without_files(workdir: Path) -> None:
    (workdir / "broken.pdf").write_bytes(b"%PDF-1.4 broken")
    run_batch(plan_batch([workdir / "broken.pdf"]), overwrite=YES)
    assert f"## {load_catalog('en').text('summary.where_title')}" not in summary(workdir)


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_09_texts(language: str) -> None:
    catalog = load_catalog(language)
    for key in ("summary.cleaned", "gui.result.stat_kept", "gui.help.tools_title"):
        assert catalog.text(key)
    assert catalog.plural("summary.count.kept", 2)
