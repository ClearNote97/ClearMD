"""Feature 025 — "Split the Large PDFs" from Convert (spec/features/025_*/spec.md): the offer on
Review and Results, the action, and the recommended number of parts."""

from dataclasses import replace
from pathlib import Path

import pytest
from support.gui_fakes import FakeBackend, planned
from support.presenter_fakes import make, state

from clearmd.backend.api import Cut, Keep, SplitSpec
from clearmd.backend.schemas.errors import ErrorCode, SkipReason
from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus, PlanWarning, SkippedItem
from clearmd.backend.use_cases.split_advice import large_in_plan, recommended_parts
from clearmd.frontend.presenter.state import Tool

LIMIT = 600.0
GIB = 1024**3


def slow(name: str, seconds: float) -> PlanWarning:
    return PlanWarning(replace(planned(name), cost=seconds), seconds, LIMIT)


def plan_with_large() -> BatchPlan:
    big, docx = slow("big.pdf", 2400.0), slow("big.docx", 2400.0)
    heavy = SkippedItem(
        Path("/docs/heavy.pdf"), SkipReason.TOO_MUCH_MEMORY, measured=9 * GIB, limit=4 * GIB
    )
    return BatchPlan((big.item, docx.item), (heavy,), (), (big, docx))


@pytest.mark.parametrize(
    ("arguments", "parts"),
    [
        ({"seconds": 2400.0, "time_limit": LIMIT}, 7),  # 2400 / 360 = 6.7
        ({"seconds": 100.0, "time_limit": LIMIT}, 2),  # never fewer than 2
        ({"memory": 9 * GIB, "memory_limit": 4 * GIB}, 4),  # 9 / 2.4 = 3.75
        ({"seconds": 1e9, "time_limit": LIMIT}, 1000),  # never more than 1,000
        ({"seconds": 2400.0, "time_limit": LIMIT, "memory": 30 * GIB, "memory_limit": 4 * GIB}, 13),
    ],
)
def test_ac_03_the_recommendation_fits_the_limits_with_a_margin(
    arguments: dict[str, float], parts: int
) -> None:
    assert recommended_parts(**arguments) == parts


def test_ac_01_review_offers_it_for_large_pdfs_only() -> None:
    found = dict(large_in_plan(plan_with_large()))
    assert found == {Path("/docs/big.pdf"): 7, Path("/docs/heavy.pdf"): 4}  # not the .docx
    presenter, view, _, _ = make(FakeBackend(plan=plan_with_large()))
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert view.last("plan").split_offer == "Split the Large PDFs (2)"


def test_ac_01_no_offer_without_large_pdfs() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert view.last("plan").split_offer == ""


def test_ac_02_the_action_opens_split_with_them_and_the_recommendation() -> None:
    presenter, view, fake, _ = make(FakeBackend(plan=plan_with_large()))
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    presenter.split_large()
    shown = state(view)
    assert (shown.page, shown.tool) == (1, Tool.SPLIT)
    assert [row.name for row in view.last("inputs")] == ["big.pdf", "heavy.pdf"]
    settings = presenter.settings  # for this task only: never saved as a choice (audit v3)
    assert (settings.split_cut, settings.split_parts, settings.split_keep) == (
        "parts",
        7,
        "markdown",
    )
    assert all(saved.split_parts != 7 for saved in fake.saved)
    presenter.analyze()  # the user goes on: Split's plan with the recommended cut
    view.drain()
    assert fake.plan_calls[-1]["split"] == SplitSpec(Cut.PARTS, 7, Keep.MARKDOWN)


def test_ac_01_results_offer_it_for_the_pdfs_stopped_at_a_limit() -> None:
    backend = FakeBackend(statuses={"a.pdf": OutcomeStatus.STOPPED})
    presenter, view, _, _ = make(backend)
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    presenter.confirm()
    view.drain()
    result = view.last("result")
    assert result.split_offer == "Split the Large PDFs (1)"
    presenter.split_large()
    assert state(view).tool is Tool.SPLIT


def test_ac_04_its_label_in_both_languages() -> None:
    from clearmd.i18n import load_catalog

    assert load_catalog("en").text("gui.offer.split", count=2) == "Split the Large PDFs (2)"
    assert load_catalog("es").text("gui.offer.split", count=2) == "Dividir los PDF Muy Grandes (2)"
    assert ErrorCode.TIMED_OUT.action_key  # the stop's own advice stays
