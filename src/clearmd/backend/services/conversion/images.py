"""The images of a document, kept in a folder next to its Markdown (feature 012, ADR-0033).

A converter hands each image's bytes to an ``ImageSink``; the sink names it (``image-001.png``:
never a name from the document), checks it is a picture a Markdown viewer shows (by its bytes,
not its claimed type), keeps it within limits, and gives back the link to write. The worker sends
the images to the interface's process, which writes them (``use_cases.output_files``), as it
writes the Markdown: a converter never writes a file.
"""

import base64
import binascii
import hashlib
import posixpath
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

from clearmd.backend.schemas.models import ExtractedImage
from clearmd.backend.services.conversion.markdown_out import escape_text, link_target
from clearmd.backend.services.conversion.safe_files import open_regular_file

MAX_IMAGES = 1000  # per document
MAX_IMAGE_BYTES = 50 * 1024**2  # one image
MAX_TOTAL_BYTES = 200 * 1024**2  # all of a document's images
MIN_BYTES = 64  # less is no picture worth a file (a spacer, a pixel)
MAX_ENCODED_CHARS = MAX_IMAGE_BYTES * 4 // 3 + 4096  # base64 of the largest picture kept

# The pictures every Markdown viewer shows, by their first bytes.
_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"\xff\xd8\xff", "jpg"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
)
_BMP_HEADERS = {12, 40, 52, 56, 64, 108, 124}  # the sizes of a bitmap's own header
# The link of an image markitdown wrote with its data in it (docx, pptx), an optional title after
# the data. Found from its "](data:", its alt then read back to the "![" before it: any alt
# (markdownify does not escape a "]" in it), and linear however many "![" a line holds.
_DATA_TAIL = re.compile(
    r"\]\(data:image/[a-zA-Z0-9.+-]{1,20};base64,(?P<data>[A-Za-z0-9+/=\s]+?)"
    r"(?:\s+\"[^\"\n]{0,500}\")?\)"
)
MAX_ALT_CHARS = 2000
# Any data link left (a form no pattern foresaw): cut to its kind, as markitdown does by default.
_DATA_LINK = re.compile(r"\(data:(?P<kind>[a-zA-Z0-9/.+-]{1,40});base64,[A-Za-z0-9+/=\s]+")
_FOLDER_ENCODED = str.maketrans({"%": "%25", "#": "%23", "?": "%3F"})  # never a link's anchor


def kind(data: bytes) -> str | None:
    """The picture's file extension by its bytes, or None (EMF, SVG, anything else)."""
    for signature, extension in _SIGNATURES:
        if data.startswith(signature):
            return extension
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:2] == b"BM" and int.from_bytes(data[14:18], "little") in _BMP_HEADERS:
        return "bmp"
    return None


@dataclass
class ImageSink:
    """Where a converter puts a document's images. ``folder`` is the images folder's name, next
    to the Markdown (``report_images``)."""

    folder: str
    images: list[ExtractedImage]
    left_out: int = 0  # pictures in another format, or past the limits (the summary says so)
    _bytes: int = 0
    _seen: dict[bytes, str] | None = None  # a picture used again (a logo on every page): one file

    @classmethod
    def for_folder(cls, folder: str) -> "ImageSink":
        return cls(folder, [])

    def add(self, data: bytes) -> str | None:
        """The link to the kept image, relative to the Markdown, or None when it is left out."""
        if self._seen is None:
            self._seen = {}
        digest = hashlib.sha256(data).digest()
        if digest in self._seen:
            return self._seen[digest]
        extension = kind(data)
        if extension is None or len(data) < MIN_BYTES:
            self.left_out += extension is None and len(data) >= MIN_BYTES
            return None
        too_many = len(self.images) >= MAX_IMAGES
        too_big = len(data) > MAX_IMAGE_BYTES or self._bytes + len(data) > MAX_TOTAL_BYTES
        if too_many or too_big:
            self.left_out += 1
            return None
        name = f"image-{len(self.images) + 1:03d}.{extension}"
        self.images.append(ExtractedImage(name, data))
        self._bytes += len(data)
        # "Q#3 results_images": a "#" would end the path, a "%" begin an escape.
        self._seen[digest] = f"{self.folder.translate(_FOLDER_ENCODED)}/{name}"
        return self._seen[digest]


def take_data_images(markdown: str, sink: ImageSink | None) -> str:
    """Images embedded as ``data:`` URIs (how markitdown gives docx and pptx pictures) become
    files in the folder; one left out becomes its alt text, and any other data link is cut to its
    kind (as markitdown does when images are off). Without a sink, the text stays as it was."""
    if sink is None:
        return markdown

    out: list[str] = []
    done = 0
    for found in _DATA_TAIL.finditer(markdown):
        opening = markdown.rfind("![", max(done, found.start() - MAX_ALT_CHARS), found.start())
        if opening < 0 or "\n" in markdown[opening : found.start()]:
            continue  # no image starts on its line: the data link is cut below
        out.append(markdown[done:opening])
        out.append(_kept(markdown[opening + 2 : found.start()], found.group("data"), sink))
        done = found.end()
    out.append(markdown[done:])

    def cut(found: re.Match[str]) -> str:
        sink.left_out += 1
        return f"(data:{found.group('kind')};base64..."

    return _DATA_LINK.sub(cut, "".join(out))


def _kept(alt: str, encoded: str, sink: ImageSink) -> str:
    alt = " ".join(alt.split())
    data = None
    if len(encoded) <= MAX_ENCODED_CHARS:  # never decoded past the limit (review of 012)
        try:
            data = base64.b64decode("".join(encoded.split()), validate=True)
        except (binascii.Error, ValueError):
            data = None
    link = sink.add(data) if data is not None else None
    if link is None:
        if data is None:
            sink.left_out += 1
        return f"*{escape_text(alt or 'image')}*"
    return f"![{escape_text(alt)}]({link_target(link)})"


_LINKED_IMAGE = re.compile(
    r"!\[(?P<alt>[^\]\n]{0,500})\]\((?P<src>[^)\s]{1,500})(?:\s+\"[^\"\n]{0,500}\")?\)"
)
MAX_ENTRIES = 50_000  # as many as a ZIP may hold to be converted (ADR-0015)


def epub_images(source: Path, markdown: str, sink: ImageSink) -> str:
    """An EPUB's pictures, linked by the path its chapters gave (``../images/map.png``): read
    from its package by the entry whose path ends the same way the most, within the limits; a
    tie ("ch1/fig.png" and "ch2/fig.png" for "fig.png") is left as it was. Never a path outside
    the package."""
    try:
        with open_regular_file(source) as stream, zipfile.ZipFile(stream) as package:
            entries = package.infolist()
            if len(entries) > MAX_ENTRIES:
                return markdown
            by_name: dict[str, list[zipfile.ZipInfo]] = {}
            for entry in entries:
                by_name.setdefault(posixpath.basename(entry.filename), []).append(entry)
            links: dict[str, str | None] = {}  # an entry read once, however often it is shown

            def kept(found: re.Match[str]) -> str:
                src = unquote(found.group("src"))
                if ":" in src.split("/")[0]:  # http:, data:, another scheme: left as it was
                    return found.group(0)
                entry = _entry(by_name.get(posixpath.basename(src), []), src)
                if entry is None or entry.file_size > MAX_IMAGE_BYTES:
                    return found.group(0)
                if entry.filename not in links:
                    with package.open(entry) as part:
                        data = part.read(MAX_IMAGE_BYTES + 1)
                    links[entry.filename] = sink.add(data) if len(data) <= MAX_IMAGE_BYTES else None
                link = links[entry.filename]
                if link is None:
                    return found.group(0)
                return f"![{escape_text(found.group('alt'))}]({link_target(link)})"

            return _LINKED_IMAGE.sub(kept, markdown)
    except (OSError, zipfile.BadZipFile, ValueError, KeyError, RuntimeError, EOFError):
        return markdown


def _entry(candidates: list[zipfile.ZipInfo], src: str) -> zipfile.ZipInfo | None:
    """The entry whose path shares the longest ending with ``src``; None on a tie."""
    wanted = [part for part in src.split("/") if part not in ("", ".", "..")]

    def shared(entry: zipfile.ZipInfo) -> int:
        parts = entry.filename.split("/")
        count = 0
        while count < min(len(parts), len(wanted)) and parts[-1 - count] == wanted[-1 - count]:
            count += 1
        return count

    ranked = sorted(((shared(entry), entry) for entry in candidates), key=lambda pair: -pair[0])
    if not ranked or (len(ranked) > 1 and ranked[0][0] == ranked[1][0]):
        return None
    return ranked[0][1]
