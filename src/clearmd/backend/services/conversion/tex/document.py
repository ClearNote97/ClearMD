r"""One LaTeX document: its includes put in place, then rendered once (ADR-0022).

In TeX, ``\input`` inserts the file's text where it is written, so that is what happens here:
each allowed include is read once, on one budget for the whole document, and spliced in place in
document order (definitions made in it apply from there on). Includes inside comments or code
blocks are not includes; a refused one stays in the text, shown as code, with a note.
"""

import bisect
import re
from dataclasses import dataclass, field
from pathlib import Path

from clearmd.backend.schemas.models import ConversionResult
from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind, NoteReason
from clearmd.backend.services.conversion.safe_files import read_regular_file
from clearmd.backend.services.conversion.tex.context import forget_brace_pairs, mask
from clearmd.backend.services.conversion.tex.images import ImageFinder, graphics_paths
from clearmd.backend.services.conversion.tex.includes import (
    MAX_BYTES,
    IncludeState,
    enter,
    identity,
)
from clearmd.backend.services.conversion.tex.render import render_source
from clearmd.backend.services.conversion.tex.source import decode_source

_INCLUDE = re.compile(
    r"\\(input|include|subfile)(?![A-Za-z])"
    r"(?:\s*\{([^{}\n]{0,1024})\}|(?<=input)[ \t]+([^\s{}\\%]{1,1024}))"
)


@dataclass
class _Segment:
    start: int  # where it begins in the flattened text
    name: str
    source: str
    offset: int  # where it begins in its file's text


@dataclass
class _Flattened:
    parts: list[str] = field(default_factory=list)
    segments: list[_Segment] = field(default_factory=list)
    length: int = 0

    def emit(self, piece: str, name: str, source: str, offset: int) -> None:
        if piece:
            self.segments.append(_Segment(self.length, name, source, offset))
            self.parts.append(piece)
            self.length += len(piece)

    def locate(self, position: int) -> str:
        if not self.segments:
            return ""
        starts = [segment.start for segment in self.segments]
        segment = self.segments[max(0, bisect.bisect_right(starts, position) - 1)]
        local = segment.offset + position - segment.start
        return f"{segment.name}, line {segment.source.count(chr(10), 0, local) + 1}"


MAX_LISTED = 1000  # includes named in the note; the text keeps every one


class _Document:
    def __init__(self, path: Path, target: Path) -> None:
        self.path = path
        self.target = target
        self.state = IncludeState(path.parent.absolute(), stack=[identity(path)])
        self.refused: dict[NoteItem, None] = {}
        self.guessed: dict[NoteItem, None] = {}
        self.flat = _Flattened()

    def _decode(self, data: bytes, included: str | None = None) -> str:
        """The text; a guessed encoding is noted (with the file's name when it is an include)."""
        text = decode_source(data)
        if text.guessed:
            label = f"{included}: {text.encoding}" if included else text.encoding
            self.guessed[NoteItem(label)] = None
        return text.text

    def splice(self, text: str, name: str) -> None:
        cursor = 0
        for found in _INCLUDE.finditer(mask(text)):
            self.flat.emit(text[cursor : found.start()], name, text, cursor)
            cursor = found.end()
            written = found.group(2) if found.group(2) is not None else found.group(3)
            if "#" in written:  # a macro's parameter (\newcommand{\inc}[1]{\input{#1}})
                self.flat.emit(found.group(0), name, text, found.start())
                continue
            entered = enter(written, self.state)
            if isinstance(entered, NoteReason):
                if len(self.refused) < MAX_LISTED:
                    self.refused[NoteItem(written.strip(), entered.value)] = None
                self.flat.emit(found.group(0), name, text, found.start())
                continue
            included = entered.path.relative_to(self.state.folder.resolve()).as_posix()
            data = entered.data
            self.state.stack.append(entered.identity)
            try:
                # TeX ends a file with an end of line: the next word never glues to it.
                self.splice(self._decode(data, included) + "\n", included)
            finally:
                self.state.stack.pop()
        self.flat.emit(text[cursor:], name, text, cursor)

    def convert(self) -> ConversionResult:
        data = read_regular_file(self.path, MAX_BYTES)
        self.state.bytes_read = len(data)
        self.splice(self._decode(data), self.path.name)
        whole = "".join(self.flat.parts)
        finder = ImageFinder(self.state.folder, graphics_paths(mask(whole)), self.target)
        result = render_source(
            whole, image=finder.link, locate=self.flat.locate, refused=tuple(self.refused)
        )
        if not self.guessed:
            return result
        guessed = ConversionNote(NoteKind.ENCODING_GUESSED, tuple(self.guessed))
        return ConversionResult(result.markdown, (*result.notes, guessed))


def convert_document(path: Path, target: Path | None = None) -> ConversionResult:
    """Convert ``path`` and the files it includes inside its folder (ADR-0022).

    ``target`` is where the Markdown will be written: image links are relative to it (by
    default, a file next to the source).
    """
    try:
        return _Document(path, target or path.with_suffix(".md")).convert()
    finally:
        forget_brace_pairs()
