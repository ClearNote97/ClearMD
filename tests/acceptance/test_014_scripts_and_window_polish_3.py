"""Feature 014 — one test per acceptance criterion (spec/features/014_*/spec.md)."""

import time
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from support.gui_close import shut
from support.gui_fakes import FakeBackend
from support.pdf_builder import Text, build_pdf, paragraph

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.schemas.settings import Settings
from clearmd.backend.services.conversion.pdf import PdfConverter
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.layout import GUTTER, INSET

ROOT = Path(__file__).resolve().parents[2]


def converted(tmp_path: Path, page: list[Text]) -> str:
    source = tmp_path / "paper.pdf"
    source.write_bytes(build_pdf([page]))
    detection = Detection(FormatId.PDF, DetectionMethod.EXTENSION)
    return PdfConverter().convert(source, detection, tmp_path / "paper.md").markdown


def test_ac_01_an_equation_keeps_its_tall_brace(tmp_path: Path) -> None:
    markdown = converted(
        tmp_path,
        [
            *paragraph(["The set is defined as follows, for every court:"], top=700),
            Text("P(x) =", 655, 11, x=150),
            Text("{", 650, 30, x=190),
            Text("y: y <= 1", 655, 11, x=205),
            Text("(3)", 655, 11, x=520),
            *paragraph(["where the variables are the ones defined in the text above it."], top=600),
        ],
    )
    block = markdown.split("```")[1]
    assert "{" in block and "y: y <= 1" in block and "(3)" in block


def test_ac_02_scripts_are_written_as_such(tmp_path: Path) -> None:
    markdown = converted(
        tmp_path,
        [
            Text("The efficiency", 700, 11, x=72),
            Text("EF", 700, 11, x=150),
            Text("t", 704, 7, x=164.1),
            Text("o", 697, 7, x=164.1),
            Text("(x) is measured.", 700, 11, x=166.1),
            Text("The power x", 650, 11, x=72),
            Text("q", 654, 7, x=133),
            Text(" grows.", 650, 11, x=137),
        ],
    )
    assert "EFᵗₒ(x) is measured." in markdown and "x^{q}" in markdown


@pytest.fixture
def app(display: str) -> Iterator[TtkApp]:
    window = TtkApp(FakeBackend(settings=Settings(show_welcome=False, theme="light")))
    window.start()
    pump(window, seconds=0.5)
    yield window
    shut(window)


def pump(app: TtkApp, *, until: Callable[[], bool] | None = None, seconds: float = 1.0) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        app.root.update()
        if until is not None and until():
            return
        time.sleep(0.01)


def test_ac_03_one_gutter_around_and_inside_the_page(app: TtkApp) -> None:
    surface, page, rail = app.surface, app.surface.page, app.rail
    assert rail.winfo_x() == 0 and rail.winfo_width() == rail.winfo_reqwidth()
    assert page.winfo_x() == GUTTER + INSET  # the rail's gutter, then the card's inside
    right = surface.winfo_width() - (page.winfo_x() + page.winfo_width())
    bottom = surface.winfo_height() - (page.winfo_y() + page.winfo_height())
    assert right == GUTTER + INSET and bottom == GUTTER + INSET
    outline = next(i for i in surface.find_all() if str(surface.type(i)) == "polygon")
    left, top, right_edge, _ = surface.bbox(outline)
    assert abs(left - GUTTER) <= 2 and abs(surface.winfo_width() - right_edge - GUTTER) <= 2
    assert abs(page.winfo_y() - top - INSET) <= 2
    assert app.root.minsize() == (800, 624)


def test_ac_04_cards_wait_faded_with_nothing_chosen(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.go_to(2)
    pump(app, seconds=0.3)
    assert app.review.stats.dimmed and {v for _, v in app.review.stats.figures()} == {"—"}
    assert app.converting.dimmed and app.converting.ready.winfo_manager() == "pack"
    assert "—" in str(app.converting.ready_count.cget("text"))
    assert app.results.stats.dimmed and len(app.results.stats.figures()) == 3
    app.presenter.add_paths([tmp_path / "a.pdf"])
    app.presenter.analyze()  # Next on Choose: a plan, its figures shown as before
    pump(app, until=lambda: not app.review.stats.dimmed, seconds=3)
    assert not app.review.stats.dimmed and not app.converting.dimmed


def test_ac_05_screenshots_in_both_themes_and_languages() -> None:
    shots = ROOT / "docs" / "screenshots" / "014"
    for screen in ("2-review-empty", "3-convert-empty", "4-results-empty", "3-convert-ready"):
        for theme in ("light", "dark"):
            for language in ("en", "es"):
                assert (shots / f"{screen}-{theme}-{language}.png").is_file(), screen
