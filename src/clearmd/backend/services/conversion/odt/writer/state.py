"""What the writer's modules share: one run's state, the formula contract and the ``Writer``.

``OdtState`` holds everything a conversion accumulates (counters, footnotes, the growth budget, list
numbering); the modules that write one kind of element take the ``Writer`` that owns it.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from clearmd.backend.services.conversion.inline import IMAGE_WORD, InlineWriter, TextProps
from clearmd.backend.services.conversion.odt.styles import Styles
from clearmd.backend.services.conversion.odt.writer.vocab import (
    FORMULA_WORD,
    GROWTH_EXTRA,
    GROWTH_FACTOR,
    MAX_UNKNOWN,
)
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


class OdtState:
    """One run's settings, growth budget, counters and footnotes."""

    def __init__(
        self,
        styles: Styles,
        *,
        formula: FormulaHandler | None,
        language: str,
        source_size: int,
        pictures: Callable[[str], str | None] | None,
    ) -> None:
        self.styles = styles
        # A picture's link in the images folder, from its href; None: images left out (012).
        self.pictures = pictures
        self.room = GROWTH_FACTOR * source_size + GROWTH_EXTRA
        self.writer = InlineWriter(self.spend)
        self.counts = Counts()
        self.footnotes: list[str] = []
        self.formula = formula
        primary = (language or styles.language).split("-")[0]
        self.image_word = IMAGE_WORD.get(primary, "Image")
        self.formula_word = FORMULA_WORD.get(primary, "Formula")
        self.top = 1
        self.numbers: dict[tuple[str, int], int] = {}  # last number of each list style and level
        # The last top-level list written, if nothing came after it: (numbered, other markers).
        self.last_list: tuple[bool, bool] | None = None

    def spend(self, size: int) -> bool:
        """Charge ``size`` characters to the document's growth budget; ``False`` past it."""
        if size > self.room:
            self.room = 0
            return False
        self.room -= size
        return True

    def note_unknown(self, tag: str) -> None:
        """Remember an element the subset does not know (at most ``MAX_UNKNOWN`` kinds)."""
        if tag in self.counts.unknown or len(self.counts.unknown) < MAX_UNKNOWN:
            self.counts.unknown[tag] = None


class Writer(Protocol):
    """What a module that writes an element may ask of the renderer that owns it."""

    state: OdtState

    def blocks(self, elements: list[Element]) -> str:
        """The Markdown of block-level ``elements``."""
        ...

    def inline(self, paragraph: Element, props: TextProps) -> str:
        """The Markdown of a paragraph's text with ``props`` as its base properties."""
        ...
