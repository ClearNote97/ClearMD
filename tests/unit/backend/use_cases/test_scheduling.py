import random
from pathlib import Path

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod, PlannedConversion
from clearmd.backend.use_cases.scheduling import order_by_cost


def _item(name: str, cost: float) -> PlannedConversion:
    return PlannedConversion(
        source=Path("/d") / name,
        output_root=Path("/d/ClearMD_Output"),
        target=Path("/d/ClearMD_Output/OutputMD") / f"{Path(name).stem}.md",
        detection=Detection(FormatId.PDF, DetectionMethod.EXTENSION),
        exists=False,
        cost=cost,
    )


def test_cheapest_first_and_ties_by_path() -> None:
    items = [_item("big.pdf", 600), _item("b.txt", 1), _item("A.txt", 1), _item("mid.docx", 30)]
    ordered = [item.source.name for item in order_by_cost(items)]
    assert ordered == ["A.txt", "b.txt", "mid.docx", "big.pdf"]


def test_order_does_not_depend_on_the_input_order() -> None:
    items = [_item(f"f{i}.pdf", cost) for i, cost in enumerate([5, 1, 5, 3, 1, 9])]
    expected = order_by_cost(items)
    for seed in range(10):
        shuffled = items[:]
        random.Random(seed).shuffle(shuffled)
        assert order_by_cost(shuffled) == expected


def test_nothing_to_order() -> None:
    assert order_by_cost([]) == ()
