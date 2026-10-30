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
from clearmd.backend.services.conversion.markdown_out import MARK, escape_text, link_target
from clearmd.backend.services.conversion.safe_files import open_regular_file

MAX_IMAGES = 1000  # per document
MAX_IMAGE_BYTES = 50 * 1024**2  # one image
MAX_TOTAL_BYTES = 200 * 1024**2  # all of a document's images
MIN_BYTES = 64  # less is no picture worth a file (a spacer, a pixel)

# The pictures every Markdown viewer shows, by their first bytes.
_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"\xff\xd8\xff", "jpg"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
    (b"BM", "bmp"),
)
_DATA_IMAGE = re.compile(
    r"!\[(?P<alt>[^\]\n]{0,500})\]\(data:image/[a-zA-Z0-9.+-]{1,20};base64,(?P<data>[A-Za-z0-9+/=\s]+)\)"
)


def kind(data: bytes) -> str | None:
    """The picture's file extension by its bytes, or None (EMF, SVG, anything else)."""
    for signature, extension in _SIGNATURES:
        if data.startswith(signature):
            return extension
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
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
        self._seen[digest] = f"{self.folder}/{name}"
        return self._seen[digest]

    def markdown(self, data: bytes, alt: str) -> str | None:
        """``![alt](folder/image-001.png)``, a block ClearMD writes itself, or None."""
        link = self.add(data)
        if link is None:
            return None
        return f"{MARK}![{escape_text(' '.join(alt.split()))}]({link_target(link)})"


def take_data_images(markdown: str, sink: ImageSink | None) -> str:
    """Images embedded as ``data:`` URIs (how markitdown gives docx and pptx pictures) become
    files in the folder; without a sink, or when one is left out, its text stays as it was."""
    if sink is None:
        return markdown

    def kept(found: re.Match[str]) -> str:
        try:
            data = base64.b64decode("".join(found.group("data").split()), validate=True)
        except (binascii.Error, ValueError):
            return found.group(0)
        link = sink.add(data)
        if link is None:
            return f"*{escape_text(found.group('alt') or 'image')}*"
        return f"![{escape_text(found.group('alt'))}]({link_target(link)})"

    return _DATA_IMAGE.sub(kept, markdown)


_LINKED_IMAGE = re.compile(r"!\[(?P<alt>[^\]\n]{0,500})\]\((?P<src>[^)\s]{1,500})\)")
MAX_ENTRIES = 50_000  # as many as a ZIP may hold to be converted (ADR-0015)


def epub_images(source: Path, markdown: str, sink: ImageSink) -> str:
    """An EPUB's pictures, linked by the path its chapters gave (``../images/map.png``): read
    from its package by that file's name, within the limits; never a path outside it."""
    try:
        with open_regular_file(source) as stream, zipfile.ZipFile(stream) as package:
            entries = package.infolist()
            if len(entries) > MAX_ENTRIES:
                return markdown
            by_name: dict[str, zipfile.ZipInfo] = {}
            for entry in entries:
                by_name.setdefault(posixpath.basename(entry.filename), entry)

            def kept(found: re.Match[str]) -> str:
                src = unquote(found.group("src"))
                if ":" in src.split("/")[0]:  # http:, data:, another scheme: left as it was
                    return found.group(0)
                entry = by_name.get(posixpath.basename(src))
                if entry is None or entry.file_size > MAX_IMAGE_BYTES:
                    return found.group(0)
                with package.open(entry) as part:
                    data = part.read(MAX_IMAGE_BYTES + 1)
                link = sink.add(data[:MAX_IMAGE_BYTES]) if len(data) <= MAX_IMAGE_BYTES else None
                if link is None:
                    return found.group(0)
                return f"![{escape_text(found.group('alt'))}]({link_target(link)})"

            return _LINKED_IMAGE.sub(kept, markdown)
    except (OSError, zipfile.BadZipFile, ValueError, KeyError, RuntimeError, EOFError):
        return markdown
