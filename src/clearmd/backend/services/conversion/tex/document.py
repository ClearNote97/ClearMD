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
from clearmd.backend.services.conversion.tex.images import ImageFinder, graphics_paths
from clearmd.backend.services.conversion.tex.includes import MAX_BYTES, IncludeState, enter
from clearmd.backend.services.conversion.tex.render import render_source
from clearmd.backend.services.conversion.tex.source import decode_source

_INCLUDE = re.compile(
    r"\\(input|include|subfile)(?![A-Za-z])"
    r"(?:\s*\{([^{}\n]{0,1024})\}|(?<=input)[ \t]+([^\s{}\\%]{1,1024}))"
)
# What is not LaTeX to follow: comments, code environments and \verb.
_NOT_SOURCE = re.compile(
    r"(?<!\\)%|\\begin\s*\{(verbatim\*?|lstlisting|minted|comment)\}|\\verb\*?([^\sA-Za-z*])"
)


def mask(text: str) -> str:
    """``text`` with comments and code replaced by spaces (same length, newlines kept)."""
    pieces, cursor = [], 0
    while (found := _NOT_SOURCE.search(text, cursor)) is not None:
        if found.group(1):
            close = text.find(f"\\end{{{found.group(1)}}}", found.end())
            end = len(text) if close == -1 else close
        elif found.group(2):
            line_end = text.find("\n", found.end())
            close = text.find(
                found.group(2), found.end(), len(text) if line_end == -1 else line_end
            )
            end = found.end() if close == -1 else close + 1
        else:
            line_end = text.find("\n", found.start())
            end = len(text) if line_end == -1 else line_end
        pieces.append(text[cursor : found.start()])
        pieces.append(re.sub(r"[^\n]", " ", text[found.start() : end]))
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces)


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


class _Document:
    def __init__(self, path: Path, target: Path) -> None:
        self.path = path
        self.target = target
        self.state = IncludeState(path.parent.absolute(), stack=[path.resolve()])
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
            entered = enter(written, self.state)
            if isinstance(entered, NoteReason):
                self.refused[NoteItem(written.strip(), entered.value)] = None
                self.flat.emit(found.group(0), name, text, found.start())
                continue
            real, data = entered
            included = real.relative_to(self.state.folder.resolve()).as_posix()
            self.state.stack.append(real)
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
    return _Document(path, target or path.with_suffix(".md")).convert()
