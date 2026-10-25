"""ClearMD's own LaTeX converter (feature 002, ADR-0006, ADR-0022). Worker process only."""

from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.models import ConversionResult, Detection
from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind
from clearmd.backend.services.conversion.safe_files import read_regular_file
from clearmd.backend.services.conversion.tex.render import render_latex
from clearmd.backend.services.conversion.tex.source import decode_source

MAX_SOURCE_BYTES = Limits().max_file_size


class TexConverter:
    """Read → decode → render (includes and the author's macros: slice B of feature 002)."""

    def convert(self, source: Path, detection: Detection) -> ConversionResult:
        try:
            data = read_regular_file(source, MAX_SOURCE_BYTES)
        except OSError as error:
            detail = f"{type(error).__name__}: {error}"
            raise ConversionError(ErrorCode.SOURCE_UNREADABLE, detail) from error
        text = decode_source(data)
        result = render_latex(text.text)
        if not text.guessed:
            return result
        guessed = ConversionNote(NoteKind.ENCODING_GUESSED, (NoteItem(text.encoding),))
        return ConversionResult(result.markdown, (*result.notes, guessed))
