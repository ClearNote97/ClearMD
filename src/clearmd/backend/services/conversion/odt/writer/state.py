"""What the writer's modules share: the formula contract and one run's counters."""

from collections.abc import Callable
from dataclasses import dataclass, field

from clearmd.backend.services.conversion.xmltree import Element

# A formula object → its LaTeX (without $), or ``None`` with the source to show instead
# (StarMath, or nothing) when it is not converted; ``formula`` is false for a chart or another
# embedded object, which is shown as an image placeholder.
FormulaHandler = Callable[[Element], "FormulaResult"]


@dataclass(frozen=True)
class FormulaResult:
    latex: str | None
    source: str | None = None
    formula: bool = True


@dataclass
class Counts:
    images: int = 0
    formulas_kept: int = 0
    comments: int = 0
    changes: int = 0
    tables_simplified: int = 0
    unknown: dict[str, None] = field(default_factory=dict)
