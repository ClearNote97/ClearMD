"""The pieces inline text is made of: runs of text with their properties, and raw Markdown."""

from dataclasses import dataclass

LINE_BREAK = "  \n"
# The image placeholder's word in the document's language (English otherwise).
IMAGE_WORD = {"es": "Imagen", "pt": "Imagem", "fr": "Image", "it": "Immagine", "de": "Bild"}


@dataclass(frozen=True)
class TextProps:
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    position: str = ""  # "super", "sub" or ""
    mono: bool = False
    hidden: bool = False


@dataclass(frozen=True)
class Text:
    text: str
    props: TextProps
    link: str | None
    literal: bool = False  # spaces and tabs written as such (text:s, text:tab): never collapsed


@dataclass(frozen=True)
class Raw:
    markdown: str  # written by ClearMD itself: a footnote reference, a line break, a placeholder


Piece = Text | Raw


def split_space(text: str) -> tuple[str, str, str]:
    core = text.strip(" \t")
    if not core:
        return text, "", ""
    start = text.index(core)
    return text[:start], core, text[start + len(core) :]
