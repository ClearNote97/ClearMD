"""What the writer's modules share: the limits, the tags, one run's state and the ``Writer``.

Every limit that bounds what a page may make ClearMD write lives here (except ``MAX_CELLS``, which
the table writer owns). ``ArticleState`` holds what a conversion accumulates (growth budget, nesting
depth, list markers, counters); the modules that write one kind of element take the ``Writer``.
"""

from typing import Any, Protocol

from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind
from clearmd.backend.services.conversion.inline import IMAGE_WORD, InlineWriter
from clearmd.backend.services.conversion.xmltree import Element

GROWTH_FACTOR = 4
GROWTH_EXTRA = 1024**2
MAX_NESTING = 32  # quotes, tables and divisions inside each other
MAX_LIST_LEVEL = 10  # a list nested deeper is written as its text
MAX_UNKNOWN = 1000
# hi@rend → the property it sets.
HI: dict[str, dict[str, Any]] = {
    "#b": {"bold": True}, "#i": {"italic": True}, "#u": {"underline": True},
    "#t": {"mono": True}, "#sup": {"position": "super"}, "#sub": {"position": "sub"},
}  # fmt: skip
BLOCKS = frozenset({"head", "p", "list", "quote", "code", "table", "div", "ab"})


class ArticleState:
    """One run's growth budget, nesting depth, list markers and counters."""

    def __init__(self, *, language: str, source_size: int) -> None:
        self.image_word = IMAGE_WORD.get(language.split("-")[0].lower(), "Image")
        self.room = GROWTH_FACTOR * source_size + GROWTH_EXTRA
        self.writer = InlineWriter(self.spend)
        self.top = 1
        self.depth = 0
        self.last_list: tuple[bool, bool] | None = None  # (numbered, other markers)
        self.images = 0
        self.tables_simplified = 0
        self.unknown: dict[str, None] = {}

    def spend(self, size: int) -> bool:
        """Charge ``size`` characters to the document's growth budget; ``False`` past it."""
        if size > self.room:
            self.room = 0
            return False
        self.room -= size
        return True

    def note_unknown(self, tag: str) -> None:
        """Remember an element the subset does not know (at most ``MAX_UNKNOWN`` kinds)."""
        if tag in self.unknown or len(self.unknown) < MAX_UNKNOWN:
            self.unknown[tag] = None


class Writer(Protocol):
    """What a module that writes an element may ask of the renderer that owns it."""

    state: ArticleState

    def blocks(self, children: list[Element | str]) -> str:
        """The Markdown of the block-level ``children``."""
        ...


def collect_notes(w: Writer) -> tuple[ConversionNote, ...]:
    found: list[ConversionNote] = []
    if w.state.images:
        found.append(
            ConversionNote(NoteKind.IMAGES_NOT_DOWNLOADED, (NoteItem(str(w.state.images)),))
        )
    if w.state.writer.dropped:
        count = NoteItem(str(w.state.writer.dropped))
        found.append(ConversionNote(NoteKind.FORMATTING_DROPPED, (count,)))
    if w.state.tables_simplified:
        count = NoteItem(str(w.state.tables_simplified))
        found.append(ConversionNote(NoteKind.TABLE_SIMPLIFIED, (count,)))
    if w.state.unknown:
        items = tuple(NoteItem(tag) for tag in w.state.unknown)
        found.append(ConversionNote(NoteKind.ELEMENTS_SIMPLIFIED, items))
    return tuple(found)
