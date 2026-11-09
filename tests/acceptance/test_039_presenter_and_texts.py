"""Feature 039, the presenter's and the texts' part: numbers that agree, words beside colours,
an edit that goes back to step 1, Undo, the language at once, and texts that say the truth."""

import re
from pathlib import Path

import pytest
from support.gui_fakes import FakeBackend, planned
from support.presenter_fakes import make

from clearmd.backend.schemas.models import BatchPlan
from clearmd.frontend.presenter.intents.reset import unexpected
from clearmd.frontend.presenter.screens.convert import progress_view
from clearmd.frontend.presenter.screens.help import help_sections
from clearmd.frontend.presenter.screens.review import plan_view
from clearmd.frontend.presenter.state import AppState
from clearmd.i18n import load_catalog

ROOT = Path(__file__).resolve().parents[2]
LANGUAGES = ["en", "es"]


def test_ac_07_review_counts_each_file_once() -> None:
    catalog = load_catalog("es")
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf", exists=True)), (), ())
    view = plan_view(catalog, plan, "ask", 1)
    figures = {stat.label: stat.value for stat in view.stats}
    assert figures[catalog.text("gui.plan.stat_convert")] == 1
    assert figures[catalog.text("gui.plan.stat_existing_one")] == 1


def test_ac_07_an_error_says_how_far_it_got_never_zero(workdir: Path) -> None:
    plan = BatchPlan((planned("a.pdf", folder=workdir), planned("b.pdf", folder=workdir)), (), ())
    presenter, view, _, _ = make(FakeBackend(plan=plan))
    presenter.add_paths([workdir / "a.pdf"])
    presenter.analyze()
    view.drain()
    presenter._session.state = AppState.CONVERTING
    presenter._session.done = 1
    unexpected(presenter._session, presenter._display, RuntimeError("boom"))
    result = view.last("result")
    assert result.stats == () and "1" in result.counts and "2" in result.counts


def test_ac_05_the_bar_moves_inside_a_long_file() -> None:
    catalog = load_catalog("en")
    current = (1, 2, "big.pdf", None, "pdf")
    assert progress_view(catalog, current, 0, 1.0, (50, 100)).fraction == pytest.approx(0.25)


def test_ac_05_split_the_large_pdfs_gives_the_list_back() -> None:
    from dataclasses import replace

    from clearmd.backend.schemas.models import PlanWarning
    from clearmd.frontend.presenter.state import Tool

    big = PlanWarning(replace(planned("big.pdf"), cost=2400.0), 2400.0, 600.0)
    small = planned("a.docx")
    plan = BatchPlan((big.item, small), (), (), (big,))
    presenter, view, fake, _ = make(FakeBackend(plan=plan))
    presenter.add_paths([Path("/docs/big.pdf"), Path("/docs/a.docx")])
    presenter.analyze()
    view.drain()
    presenter.split_large()
    assert presenter.tool is Tool.SPLIT
    assert all(saved.split_parts != presenter.settings.split_parts for saved in fake.saved)
    presenter.choose_tool(Tool.CONVERT)
    assert [p.name for p in presenter._session.inputs] == ["a.docx"]


def test_ac_10_clear_all_can_be_undone() -> None:
    presenter, view, _, _ = make()
    paths = [Path("/docs/a.pdf"), Path("/docs/b.pdf")]
    presenter.add_paths(paths)
    presenter.clear_inputs()
    assert view.last("undo")
    presenter.undo_clear()
    assert [p.name for p in presenter._session.inputs] == ["a.pdf", "b.pdf"]
    assert view.last("undo") is None


def test_ac_04_the_welcome_switches_the_language() -> None:
    presenter, _, backend, _ = make()
    presenter.choose_language("es")
    assert presenter.settings.language == "es" and backend.saved[-1].language == "es"
    assert presenter.catalog.language == "es"


@pytest.mark.parametrize("language", LANGUAGES)
def test_ac_04_help_guides_to_the_ai_and_to_step_1(language: str) -> None:
    catalog = load_catalog(language)
    titles = [title for title, _ in help_sections(catalog, drops=True)]
    assert catalog.text("gui.help.ai_title") in titles
    assert "Settings" not in catalog.text("gui.help.where")
    assert "Ajustes" not in catalog.text("gui.help.where")
    assert "nienvasa@gmail.com" in catalog.text_template("report.how")
    assert "/discussions" in catalog.text_template("report.how")


FORBIDDEN = re.compile(r"one file|un solo archivo|unpacks|descomprim|made with|hecha con|LGPL")


def test_ac_03_the_installer_says_what_is_true() -> None:
    texts = "\n".join(
        line
        for name in ("clearmd.iss", "look/painted.iss")
        for line in (ROOT / "packaging" / "installer" / name).read_text("utf-8-sig").splitlines()
        if re.match(r"(english|spanish)\.(Card|Compare)", line)
    )
    assert not FORBIDDEN.search(texts), FORBIDDEN.search(texts)
    script = (ROOT / "packaging" / "installer" / "clearmd.iss").read_text("utf-8-sig")
    assert "postinstall skipifsilent" in script and "{cm:LaunchNow}" in script


def test_ac_03_the_download_page_names_every_file_and_this_version_only() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("notes", ROOT / "packaging" / "release_notes.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    notes = (ROOT / "packaging" / "RELEASE_NOTES.md").read_text("utf-8")
    page = module.published(notes)
    assert page.count("**New in ") == 1
    for name in ("ClearMD-Setup-<version>.exe", "ClearMD-Setup-Full-<version>.exe", "SHA256SUMS"):
        assert name in page
    for words in ("screen reader", "lector de pantalla", "More info → Run anyway"):
        assert words in page
    assert "delete the file; nothing else is installed" not in notes
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text("utf-8")
    assert "release_notes.py" in workflow and "Sign the installers" in workflow


@pytest.mark.parametrize("readme", ["README.md", "README.es.md"])
def test_ac_03_the_readme_tells_screen_reader_users_which_file(readme: str) -> None:
    text = (ROOT / readme).read_text("utf-8")
    assert "ClearMD-Setup-Full" in text and (
        "screen reader" in text or "lector de pantalla" in text
    )


def test_ac_11_hidden_pdf_text_is_an_adr() -> None:
    adr = (ROOT / "docs" / "decisions" / "0054-hidden-pdf-text.md").read_text("utf-8")
    assert "OCR" in adr and "white" in adr.lower()
