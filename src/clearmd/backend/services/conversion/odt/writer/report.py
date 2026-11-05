"""The notes a run earned, from the counters it kept.

It stands alone because nothing else reads all the counters: it is the end of every conversion.
"""

from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind, NoteReason
from clearmd.backend.services.conversion.odt.writer.state import Writer


def collect_notes(w: Writer) -> tuple[ConversionNote, ...]:
    found: list[ConversionNote] = []
    if w.state.counts.images:
        count = NoteItem(str(w.state.counts.images))
        found.append(ConversionNote(NoteKind.IMAGES_NOT_EXTRACTED, (count,)))
    if w.state.counts.formulas_kept:
        count = NoteItem(str(w.state.counts.formulas_kept))
        found.append(ConversionNote(NoteKind.FORMULA_KEPT_AS_SOURCE, (count,)))
    if w.state.counts.unknown:
        items = tuple(NoteItem(tag) for tag in w.state.counts.unknown)
        found.append(ConversionNote(NoteKind.ELEMENTS_SIMPLIFIED, items))
    if w.state.writer.dropped:
        count = NoteItem(str(w.state.writer.dropped))
        found.append(ConversionNote(NoteKind.FORMATTING_DROPPED, (count,)))
    if w.state.counts.tables_simplified:
        count = NoteItem(str(w.state.counts.tables_simplified))
        found.append(ConversionNote(NoteKind.TABLE_SIMPLIFIED, (count,)))
    dropped = []
    if w.state.counts.comments:
        dropped.append(NoteItem(str(w.state.counts.comments), NoteReason.COMMENTS.value))
    if w.state.counts.changes:
        dropped.append(NoteItem(str(w.state.counts.changes), NoteReason.TRACKED_CHANGES.value))
    if dropped:
        found.append(ConversionNote(NoteKind.REVISIONS_DROPPED, tuple(dropped)))
    return tuple(found)
