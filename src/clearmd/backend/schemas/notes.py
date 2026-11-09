"""Conversion notes: language-neutral facts about what a converter could not do faithfully.

ADR-0022.

A note never holds a sentence: the summary and the interfaces turn it into words with the catalogs.
"""

from dataclasses import dataclass
from enum import StrEnum

MAX_SUBJECT = 200  # a subject comes from the document: a 5 MB command name must not travel whole


class NoteKind(StrEnum):
    UNKNOWN_COMMANDS = "unknown_commands"
    INCLUDE_NOT_FOLLOWED = "include_not_followed"
    MACRO_LIMIT_REACHED = "macro_limit_reached"
    TABLE_KEPT_AS_LATEX = "table_kept_as_latex"
    ENCODING_GUESSED = "encoding_guessed"
    PARSE_RECOVERED = "parse_recovered"
    ELEMENTS_SIMPLIFIED = "elements_simplified"
    TABLE_SIMPLIFIED = "table_simplified"
    REVISIONS_DROPPED = "revisions_dropped"
    IMAGES_NOT_EXTRACTED = "images_not_extracted"
    FORMULA_KEPT_AS_SOURCE = "formula_kept_as_source"
    FORMATTING_DROPPED = "formatting_dropped"
    ARTICLE_NOT_FOUND = "article_not_found"
    ARTICLE_TOO_COMPLEX = "article_too_complex"
    PAGE_CUT = "page_cut"
    IMAGES_NOT_DOWNLOADED = "images_not_downloaded"
    PDF_PAGES_WITHOUT_TEXT = "pdf_pages_without_text"
    PDF_TEXT_DECODED = "pdf_text_decoded"
    PDF_TEXT_UNREADABLE = "pdf_text_unreadable"
    PDF_RUNNING_REMOVED = "pdf_running_removed"
    IMAGES_LEFT_OUT = "images_left_out"
    # Split by words (024): parts larger than the size, a page or a paragraph that cannot be cut.
    PARTS_OVER_SIZE = "parts_over_size"
    # Split into N parts: the file allowed fewer (fewer pages, sheets or blocks than parts).
    PARTS_FEWER = "parts_fewer"
    # Text no one sees on the page (off it, tiny, invisible without a picture): ADR-0054.
    PDF_HIDDEN_TEXT_LEFT_OUT = "pdf_hidden_text_left_out"
    # Display equations ClearMD could not rebuild, kept as their characters (audit v3, B3-02).
    PDF_EQUATIONS_AS_TEXT = "pdf_equations_as_text"
    # Parts whose Markdown could not be made; their original part is kept (audit v3, B1-02).
    PARTS_NOT_CONVERTED = "parts_not_converted"
    # Remote images, unsafe links and active HTML turned into text (audit v3, B2-01).
    MADE_SAFE = "made_safe"

    @property
    def key(self) -> str:
        return f"note.{self.value}"

    @property
    def informs(self) -> bool:
        """Good news, not a problem: what ClearMD cleaned (audit 2026-11-08, B3-02)."""
        return self in INFORMATION


# Notes that tell what ClearMD tidied up: told in a calm section, never as "needs attention".
INFORMATION = frozenset(
    {NoteKind.PDF_RUNNING_REMOVED, NoteKind.PDF_TEXT_DECODED, NoteKind.MADE_SAFE}
)


class NoteReason(StrEnum):
    """Why something was not done; shown next to its subject."""

    OUTSIDE_FOLDER = "outside_folder"
    ABSOLUTE = "absolute"
    PARENT_SEGMENT = "parent_segment"
    LINK = "link"
    NOT_TEX = "not_tex"
    MISSING = "missing"
    CYCLE = "cycle"
    TOO_DEEP = "too_deep"
    TOO_MANY = "too_many"
    TOO_LARGE = "too_large"
    EXPANSIONS = "expansions"
    NESTING = "nesting"
    GROWTH = "growth"
    MADE_BY_MACRO = "made_by_macro"
    KEPT_AS_LATEX = "kept_as_latex"
    COMMENTS = "comments"
    TRACKED_CHANGES = "tracked_changes"

    @property
    def key(self) -> str:
        return f"note.reason.{self.value}"


@dataclass(frozen=True)
class NoteItem:
    """What the note is about (a command, a path, an encoding...) and, optionally, why."""

    subject: str
    reason: str = ""

    def __post_init__(self) -> None:
        if len(self.subject) > MAX_SUBJECT:
            object.__setattr__(self, "subject", self.subject[: MAX_SUBJECT - 1] + "…")


@dataclass(frozen=True)
class ConversionNote:
    kind: NoteKind
    items: tuple[NoteItem, ...] = ()
