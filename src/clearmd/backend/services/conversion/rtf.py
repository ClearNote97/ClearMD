"""Rich Text Format to Markdown, ClearMD's own reader (feature 029, ADR-0049): the text and its
paragraphs; the formatting is dropped and the summary says so. Standard library only.

RTF is groups ``{...}``, control words ``\\word123`` and text. The groups that hold no text of
the document (fonts, colours, styles, pictures, ``\\*`` destinations) are skipped; ``\\par`` ends
a paragraph; ``\\'hh`` is a byte in the document's code page; ``\\uN`` a Unicode character whose
``\\uc`` replacement characters are skipped.
"""

import re
from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.models import ConversionResult, Detection
from clearmd.backend.schemas.notes import ConversionNote, NoteKind
from clearmd.backend.services.conversion.safe_files import NotARegularFile, read_regular_file

MAX_BYTES = 64 * 1024**2
_SKIPPED = frozenset(
    {"fonttbl", "colortbl", "stylesheet", "info", "pict", "object", "header", "footer",
     "headerl", "headerr", "footerl", "footerr", "listtable", "listoverridetable", "themedata",
     "colorschememapping", "latentstyles", "datastore", "xmlnstbl", "rsidtbl", "generator",
     "fldinst", "bkmkstart", "bkmkend", "filetbl", "revtbl", "pgdsctbl", "shppict"}
)  # fmt: skip
_TOKEN = re.compile(
    rb"\\([a-zA-Z]+)(-?\d+)? ?|\\'([0-9a-fA-F]{2})|\\(.)|([{}])|([\r\n]+)|([^\\{}\r\n]+)",
    re.DOTALL,
)
_BREAKS = {"par": "\n\n", "line": "\n", "tab": "\t", "row": "\n", "cell": " | ", "page": "\n\n"}
_CHARACTERS = {
    "emdash": "\u2014", "endash": "\u2013", "bullet": "\u2022", "lquote": "\u2018",
    "rquote": "\u2019", "ldblquote": "\u201c", "rdblquote": "\u201d", "~": "\u00a0",
}  # fmt: skip


def rtf_text(data: bytes) -> str:
    """The text of an RTF document, paragraphs separated by a blank line."""
    if not data.lstrip().startswith(b"{\\rtf"):
        raise ConversionError(ErrorCode.CORRUPT_FILE, "not an RTF document")
    codepage = "cp1252"
    found = re.search(rb"\\ansicpg(\d+)", data[:4096])
    if found:
        codepage = f"cp{int(found.group(1))}"
    out: list[str] = []
    stack: list[tuple[bool, int]] = []  # (skipping, uc) of the enclosing groups
    skipping, uc, pending_skip, first = False, 1, 0, False
    for word, number, hexa, symbol, brace, _breaks, text in (
        m.groups() for m in _TOKEN.finditer(data)
    ):
        if brace == b"{":
            stack.append((skipping, uc))
            first = True
            continue
        if brace == b"}":
            skipping, uc = stack.pop() if stack else (skipping, uc)
            first = False
            continue
        starts_group, first = first, False
        if word is not None:
            name = word.decode("ascii")
            if starts_group and name in _SKIPPED:
                skipping = True
            elif name == "uc" and number is not None:
                uc = int(number)
            elif skipping:
                pass
            elif name == "u" and number is not None:
                out.append(chr(int(number) % 65536))
                pending_skip = uc
            elif name in _BREAKS:
                out.append(_BREAKS[name])
            elif name in _CHARACTERS:
                out.append(_CHARACTERS[name])
            continue
        if symbol is not None:
            if symbol == b"*" and starts_group:
                skipping = True
            elif not skipping and symbol in (b"\\", b"{", b"}"):
                out.append(symbol.decode())
            elif not skipping and symbol == b"~":
                out.append("\u00a0")
            continue
        if skipping:
            continue
        if hexa is not None:
            if pending_skip:
                pending_skip -= 1
                continue
            out.append(bytes([int(hexa, 16)]).decode(codepage, errors="replace"))
        elif text is not None:
            chunk = text.decode(codepage, errors="replace")
            if pending_skip:
                chunk = chunk[pending_skip:]
                pending_skip = 0
            out.append(chunk)
    paragraphs = re.split(r"\n\s*\n", "".join(out))
    return "\n\n".join(p.strip() for p in paragraphs if p.strip())


class RtfConverter:
    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        try:
            data = read_regular_file(source, MAX_BYTES)
        except (OSError, NotARegularFile) as error:
            raise ConversionError(ErrorCode.SOURCE_UNREADABLE, str(error)) from error
        text = rtf_text(data)
        notes = (ConversionNote(NoteKind.FORMATTING_DROPPED),)
        return ConversionResult(text + "\n" if text else "", notes)
