"""How documents are merged (feature 026, ADR-0046): into one Markdown or one PDF."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class Into(StrEnum):
    MARKDOWN = "markdown"  # every document converted (Markdown taken as it is), then joined
    PDF = "pdf"  # only PDFs: their pages copied whole, in order

    @property
    def suffix(self) -> str:
        return ".md" if self is Into.MARKDOWN else ".pdf"


@dataclass(frozen=True)
class MergeSpec:
    into: Into
    # The merged file in OutputUnif. Planning names it with the time; the run, in the user's
    # language ("Merged 2026-11-08 10-30").
    target: Path = Path()
    stamp: str = ""
    # The visible line that opens each document in a merged Markdown (audit 2026-11-08, B3-08),
    # in the user's language.
    heading: str = "Document {index} of {total}: {name}"
