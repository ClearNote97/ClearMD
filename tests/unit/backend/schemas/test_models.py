from pathlib import Path

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import (
    BatchPlan,
    Detection,
    DetectionMethod,
    PlannedConversion,
    SkippedItem,
)


def _planned(
    name: str, *, root: str = "/d/ClearMD_Output", exists: bool = False
) -> PlannedConversion:
    return PlannedConversion(
        source=Path("/d") / name,
        output_root=Path(root),
        target=Path(root) / "Output" / f"{Path(name).stem}.md",
        detection=Detection(FormatId.PDF, DetectionMethod.EXTENSION),
        exists=exists,
        cost=1.0,
    )


def test_empty_plan_has_nothing_to_do() -> None:
    plan = BatchPlan(conversions=(), skipped=(), input_errors=())
    assert plan.is_empty
    assert plan.existing == ()
    assert plan.output_roots == ()


def test_plan_lists_existing_outputs_and_output_roots_in_order() -> None:
    first = _planned("a.pdf", exists=True)
    second = _planned("b.pdf", root="/e/ClearMD_Output")
    third = _planned("c.pdf")
    plan = BatchPlan(
        conversions=(first, second, third),
        skipped=(SkippedItem(Path("/d/.git"), SkipReason.HIDDEN, is_dir=True),),
        input_errors=(),
    )
    assert not plan.is_empty
    assert plan.existing == (first,)
    assert plan.output_roots == (Path("/d/ClearMD_Output"), Path("/e/ClearMD_Output"))


def test_detection_knows_how_it_was_made() -> None:
    assert Detection(FormatId.DOCX, DetectionMethod.CONTENT).by_content
    assert not Detection(FormatId.DOCX, DetectionMethod.EXTENSION).by_content
