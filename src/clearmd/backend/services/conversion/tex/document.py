"""One LaTeX document, its includes and (feature 002, T07) its macros, rendered to Markdown."""

import re
from pathlib import Path

from clearmd.backend.schemas.models import ConversionResult
from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind, NoteReason
from clearmd.backend.services.conversion.safe_files import read_regular_file
from clearmd.backend.services.conversion.tex.context import make_context, parse
from clearmd.backend.services.conversion.tex.images import graphics_paths, image_link
from clearmd.backend.services.conversion.tex.includes import MAX_BYTES, IncludeState, enter
from clearmd.backend.services.conversion.tex.render import Renderer, author_macros
from clearmd.backend.services.conversion.tex.source import decode_source

_INCLUDE = re.compile(r"\\(?:input|include|subfile)\s*\{([^}]*)\}")
_COMMENT = re.compile(r"(?<!\\)%.*")


class _Document:
    def __init__(self, path: Path, target: Path) -> None:
        self.path = path
        self.target = target
        self.state = IncludeState(path.parent.absolute(), stack=[path.resolve()])
        self.refused: dict[NoteItem, None] = {}
        self.guessed: dict[NoteItem, None] = {}
        self.parse_errors: dict[NoteItem, None] = {}
        self.context = make_context()
        self.renderer: Renderer | None = None

    def _decode(self, data: bytes, included: str | None = None) -> str:
        """The text; a guessed encoding is noted (with the file's name when it is an include)."""
        text = decode_source(data)
        if text.guessed:
            label = f"{included}: {text.encoding}" if included else text.encoding
            self.guessed[NoteItem(label)] = None
        return text.text

    def gather(self, text: str) -> str:
        """Every allowed include's text, once, for document-wide facts (heading levels, macros)."""
        state = IncludeState(self.state.folder, stack=list(self.state.stack))
        texts = [text]

        def walk(source: str) -> None:
            for argument in _INCLUDE.findall(_COMMENT.sub("", source)):
                entered = enter(argument, state)
                if isinstance(entered, NoteReason):
                    continue
                real, data = entered
                included = decode_source(data).text
                texts.append(included)
                state.stack.append(real)
                walk(included)
                state.stack.pop()

        walk(text)
        return "\n".join(texts)

    def include(self, argument: str) -> str | None:
        entered = enter(argument, self.state)
        if isinstance(entered, NoteReason):
            self.refused[NoteItem(argument.strip(), entered.value)] = None
            return None
        real, data = entered
        name = real.relative_to(self.state.folder.resolve()).as_posix()
        nodes, error = parse(self._decode(data, name), self.context)
        if error:
            self.parse_errors[NoteItem(f"{name}: {error}")] = None
        assert self.renderer is not None
        self.state.stack.append(real)
        try:
            return self.renderer.render(nodes)
        finally:
            self.state.stack.pop()

    def convert(self) -> ConversionResult:
        data = read_regular_file(self.path, MAX_BYTES)
        self.state.bytes_read = len(data)
        text = self._decode(data)
        whole = self.gather(text)
        macros = author_macros(parse(whole, self.context, strict=False)[0], len(whole))
        if macros is not None:
            self.context = macros.context
        prefixes = graphics_paths(whole)
        folder = self.state.folder

        def image(argument: str) -> str:
            return image_link(argument, folder, prefixes, self.target)

        self.renderer = Renderer(whole, include=self.include, image=image, macros=macros)
        nodes, error = parse(text, self.context)
        if error:
            self.parse_errors[NoteItem(error)] = None
        markdown = self.renderer.document(nodes)
        notes = list(self.renderer.notes())
        if self.refused:
            notes.append(ConversionNote(NoteKind.INCLUDE_NOT_FOLLOWED, tuple(self.refused)))
        if self.guessed:
            notes.append(ConversionNote(NoteKind.ENCODING_GUESSED, tuple(self.guessed)))
        if self.parse_errors:
            notes.append(ConversionNote(NoteKind.PARSE_RECOVERED, tuple(self.parse_errors)))
        return ConversionResult(markdown, tuple(notes))


def convert_document(path: Path, target: Path | None = None) -> ConversionResult:
    """Convert ``path`` and the files it includes inside its folder (ADR-0022).

    ``target`` is where the Markdown will be written: image links are relative to it (by
    default, a file next to the source).
    """
    return _Document(path, target or path.with_suffix(".md")).convert()
