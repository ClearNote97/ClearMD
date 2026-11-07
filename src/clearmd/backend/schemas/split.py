"""How a file is split (feature 023, ADR-0044): the cut, its size and what is kept."""

from dataclasses import dataclass
from enum import StrEnum


class Cut(StrEnum):
    PARTS = "parts"  # into N parts, as even as possible
    PAGES = "pages"  # every N pages; the last part may be shorter
    WORDS = "words"  # parts of about N words, to fit an AI (feature 024, ADR-0045)


class Keep(StrEnum):
    PDF = "pdf"  # the parts in their own format
    MARKDOWN = "markdown"  # each part's Markdown alone
    BOTH = "both"

    @property
    def markdown(self) -> bool:
        return self is not Keep.PDF

    @property
    def original(self) -> bool:
        return self is not Keep.MARKDOWN


MIN_PARTS = 2
MIN_PAGES = 1
MAX_SIZE = 10_000
MIN_WORDS = 500
MAX_WORDS = 1_000_000


BOUNDS = {
    Cut.PARTS: (MIN_PARTS, MAX_SIZE),
    Cut.PAGES: (MIN_PAGES, MAX_SIZE),
    Cut.WORDS: (MIN_WORDS, MAX_WORDS),
}


@dataclass(frozen=True)
class SplitSpec:
    cut: Cut
    size: int  # the number of parts, or of pages per part
    keep: Keep = Keep.BOTH
    # A part's name without extension, in the user's language: "{name} - part {index} of {total}".
    part_name: str = "{name} - part {index} of {total}"

    def __post_init__(self) -> None:
        low, high = BOUNDS[self.cut]
        if not low <= self.size <= high:
            raise ValueError(f"{self.cut.value} must be between {low} and {high}: {self.size}")
