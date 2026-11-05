r"""What the writer's modules share: one run's counters and notes, and the writer's contract.

``RenderState`` holds everything a conversion accumulates (unknown commands, refused includes,
footnotes, metadata, how deep inside ``\texttt`` it is) and the settings it was started with. The
modules that write one kind of node take it, or the ``Writer`` that owns it, as first argument.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any, Protocol

from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind
from clearmd.backend.services.conversion.markdown_out import MARK, escape_text
from clearmd.backend.services.conversion.tex.images import name_only_image
from clearmd.backend.services.conversion.tex.macros import MacroExpander
from clearmd.backend.services.conversion.tex.writer.vocab import MAX_UNKNOWN

# The link target for an image argument, or ``None`` when it must not become a link (ADR-0022).
ImageHandler = Callable[[str], str | None]


class RenderState:
    """The settings of one conversion and what writing has noted so far."""

    def __init__(
        self,
        *,
        level: int,
        spanish: bool,
        image: ImageHandler | None,
        macros: MacroExpander | None,
        known_refused: frozenset[str],
        listed: int,
    ) -> None:
        self.level = level
        self.spanish = spanish
        self.image = image or name_only_image
        self.macros = macros
        self.unknown: dict[str, None] = {}
        self.refused: dict[NoteItem, None] = {}
        self.tables_kept = 0
        self.footnotes: list[str] = []
        self.metadata: dict[str, list[Any]] = {}
        self.consumed: set[int] = set()  # captions already shown by their float
        self.alt: list[str] = []  # the caption of the float whose only image is being drawn
        self.known_refused = known_refused  # includes already noted while reading
        self.listed = listed  # how many of them: the note lists at most MAX_UNKNOWN
        self.in_code = 0  # inside \\texttt: text as written, no escaping, no ligatures
        self.recovered: dict[str, None] = {}  # what went wrong and was kept as written

    def note_unknown(self, label: str, node: Any) -> str:
        """Note a command the subset does not know and write it back as it was written."""
        if label in self.unknown or len(self.unknown) < MAX_UNKNOWN:
            self.unknown[label] = None
        return self.esc(node.latex_verbatim())

    def esc(self, text: str) -> str:
        """Document text copied as written: never a link or HTML (inside code, left as is)."""
        return text.replace(MARK, "") if self.in_code else escape_text(text)

    def knows(self, name: str) -> bool:
        """Whether ``name`` is one of the author's macros being expanded."""
        return self.macros is not None and self.macros.knows(name)

    @contextmanager
    def text_mode(self) -> Iterator[None]:
        """Text written somewhere else later (a footnote, a caption, the title) is never code,
        even when its command sits inside ``\\texttt``."""
        saved, self.in_code = self.in_code, 0
        try:
            yield
        finally:
            self.in_code = saved

    def notes(self) -> tuple[ConversionNote, ...]:
        """The notes this run earned: unknown commands, the macro limit, tables kept as LaTeX."""
        found: list[ConversionNote] = []
        if self.unknown:
            items = tuple(NoteItem(name) for name in self.unknown)
            found.append(ConversionNote(NoteKind.UNKNOWN_COMMANDS, items))
        if self.macros is not None and self.macros.exhausted is not None:
            limit = NoteItem(self.macros.limited or "", self.macros.exhausted.value)
            found.append(ConversionNote(NoteKind.MACRO_LIMIT_REACHED, (limit,)))
        if self.tables_kept:
            found.append(
                ConversionNote(NoteKind.TABLE_KEPT_AS_LATEX, (NoteItem(str(self.tables_kept)),))
            )
        return tuple(found)


class Writer(Protocol):
    """What a module that writes a node may ask of the renderer that owns it."""

    state: RenderState

    def render(self, nodes: list[Any]) -> str:
        """The Markdown of ``nodes``, block structure kept."""
        ...

    def inline(self, nodes: list[Any]) -> str:
        """The Markdown of ``nodes`` on one line."""
        ...

    def arg_nodes(self, node: Any, index: int) -> list[Any]:
        """The nodes inside argument ``index`` of ``node``."""
        ...

    def last_arg(self, node: Any) -> list[Any]:
        """The nodes inside the last argument of ``node``."""
        ...
