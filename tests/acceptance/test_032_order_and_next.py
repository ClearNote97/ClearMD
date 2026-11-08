"""Feature 032 — Merge's order and "What Next?" (spec/features/032_*/spec.md): the presenter, its
texts, and a real merge in the order chosen."""

from pathlib import Path

import pytest
from support.presenter_fakes import absolute, converted, make

from clearmd.backend.api import Into, plan_batch, run_batch
from clearmd.frontend.presenter.state import HOME, AppState, Tool
from clearmd.i18n import load_catalog


def rows(view: object) -> list[tuple[str, bool, bool]]:
    return [(row.name, row.up, row.down) for row in view.last("inputs")]  # type: ignore[attr-defined]


def test_ac_01_merge_moves_a_document_up_or_down() -> None:
    presenter, view, _, _ = make()
    presenter.choose_tool(Tool.MERGE)
    presenter.add_paths([Path("/d/a.md"), Path("/d/b.md"), Path("/d/c.md")])
    view.drain()
    assert rows(view) == [("a.md", False, True), ("b.md", True, True), ("c.md", True, False)]
    presenter.move_input(absolute("/d/c.md"), -1)
    presenter.move_input(absolute("/d/a.md"), -1)  # the first: stays
    presenter.move_input(absolute("/d/b.md"), +5)  # one place at a time only
    view.drain()
    assert [name for name, _, _ in rows(view)] == ["a.md", "c.md", "b.md"]


def test_ac_01_convert_and_split_do_not_offer_it() -> None:
    for tool in (Tool.CONVERT, Tool.SPLIT):
        presenter, view, _, _ = make()
        presenter.choose_tool(tool)
        presenter.add_paths([Path("/d/a.md"), Path("/d/b.md")])
        view.drain()
        assert all(not up and not down for _, up, down in rows(view))


def test_ac_01_moving_drops_the_plan_and_the_merge_follows_the_order(workdir: Path) -> None:
    presenter, view, fake, _ = make()
    presenter.choose_tool(Tool.MERGE)
    presenter.add_paths([Path("/d/a.md"), Path("/d/b.md")])
    presenter.analyze()
    view.drain()
    assert presenter.state is AppState.WAITING_DECISION
    presenter.move_input(absolute("/d/b.md"), -1)
    assert presenter.state in (AppState.READY,)  # the plan was made with the earlier order
    presenter.analyze()
    view.drain()
    assert fake.plan_calls[-1]["inputs"] == [absolute("/d/b.md"), absolute("/d/a.md")]
    for name in ("one", "two"):
        (workdir / f"{name}.md").write_text(f"{name} text\n", "utf-8")
    plan = plan_batch([workdir / "two.md", workdir / "one.md"], merge=Into.MARKDOWN)
    report = run_batch(plan, overwrite=lambda item: True)
    merged = next((workdir / "ClearMD_Output" / "OutputUnif").iterdir()).read_text("utf-8")
    assert merged.index("two text") < merged.index("one text")
    assert report is not None


@pytest.mark.parametrize(
    ("answer", "page", "kept"), [("keep", 1, True), ("clear", 1, False), ("home", HOME, True)]
)
def test_ac_02_what_next(answer: str, page: int, kept: bool) -> None:
    presenter, view, _, _ = converted()
    presenter.what_next(answer)
    view.drain()
    assert presenter.page == page
    assert bool(view.last("inputs")) is kept
    presenter.what_next("nonsense")  # not an answer: nothing happens
    assert presenter.page == page


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_02_and_03_texts(language: str) -> None:
    base = load_catalog(language)
    expected = {"en": "What Next?", "es": "¿Qué Sigue?"}[language]
    for tool in Tool:
        catalog = base.for_tool(tool)
        assert catalog.text("gui.result.again") == expected == catalog.text("gui.more.title")
        assert catalog.text("gui.more.home") and catalog.text("gui.main.move_up")
        assert catalog.text("gui.main.move_down") and catalog.text("gui.main.order_hint")
    intro = base.text("gui.welcome.intro").lower()
    words = {"en": ("convert", "split", "merge"), "es": ("convierte", "divide", "une")}[language]
    assert all(word in intro for word in words)
