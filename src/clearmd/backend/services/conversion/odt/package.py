"""The .odt package: its type, encryption, and parts read under a size cap (ADR-0024).

The file is opened without following a link and read through ``zipfile`` (only the entries ClearMD
needs are decompressed; pictures never are). The archive check of feature 001 already ran.
"""

import re
import zipfile
from pathlib import Path, PurePosixPath
from types import TracebackType
from typing import IO, Self

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.services.conversion.safe_files import open_regular_file
from clearmd.backend.services.conversion.xmltree import (
    Element,
    XmlLimits,
    XmlRefused,
    parse_part,
)

ODT_MIME = "application/vnd.oasis.opendocument.text"
ODF_MIME_PREFIX = "application/vnd.oasis.opendocument."
FORMULA_MIME = "application/vnd.oasis.opendocument.formula"
MAX_MIMETYPE_BYTES = 256
MAX_PART_BYTES = 256 * 1024**2  # one XML part, uncompressed
_SCHEME_OR_DRIVE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def object_part(href: str) -> str | None:
    """The archive entry of a formula object (``./Object 1`` → ``Object 1/content.xml``), or
    ``None`` when the reference leaves the archive (``..``, absolute, a scheme or a drive)."""
    name = href.strip().replace("\\", "/")
    if not name or name.startswith(("/", "~")) or _SCHEME_OR_DRIVE.match(name):
        return None
    parts = [part for part in PurePosixPath(name).parts if part not in (".", "")]
    if not parts or ".." in parts:
        return None
    return "/".join(parts) + "/content.xml"


def _entry_name(path: str) -> str:
    """A manifest path as an archive name: "./content.xml" and "/content.xml" are "content.xml"."""
    name = path.strip().replace("\\", "/")
    while name.startswith(("./", "/")):
        name = name[2:] if name.startswith("./") else name[1:]
    return name.rstrip("/")


class OdtPackage:
    def __init__(self, stream: IO[bytes], archive: zipfile.ZipFile, max_part_bytes: int) -> None:
        self._stream = stream
        self._archive: zipfile.ZipFile | None = archive
        self._max_part_bytes = max_part_bytes
        self._limits = XmlLimits()
        self._media_types: dict[str, str] = {}  # manifest entry (no "./", "/" or trailing "/")

    @classmethod
    def open(cls, path: Path, *, max_part_bytes: int = MAX_PART_BYTES) -> "OdtPackage":
        """Open and check ``path``: an OpenDocument text, not encrypted."""
        try:
            stream = open_regular_file(path)
        except OSError as error:
            raise ConversionError(
                ErrorCode.SOURCE_UNREADABLE, f"{type(error).__name__}: {error}"
            ) from error
        try:
            archive = zipfile.ZipFile(stream)
        except (zipfile.BadZipFile, OSError, ValueError) as error:
            stream.close()
            raise ConversionError(ErrorCode.CORRUPT_FILE, f"not a ZIP archive: {error}") from error
        package = cls(stream, archive, max_part_bytes)
        try:
            package._check()
        except BaseException:
            package.close()
            raise
        return package

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        trace: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        if self._archive is not None:
            self._archive.close()
            self._archive = None
        self._stream.close()

    def _zip(self) -> zipfile.ZipFile:
        if self._archive is None:
            raise ValueError("the package is closed")
        return self._archive

    def _read(self, name: str, max_bytes: int | None = None) -> bytes | None:
        archive = self._zip()
        limit = min(self._max_part_bytes, max_bytes) if max_bytes else self._max_part_bytes
        try:
            info = archive.getinfo(name)
        except KeyError:
            return None
        if info.flag_bits & 0x1:  # a ZIP-encrypted entry
            raise ConversionError(ErrorCode.PASSWORD_PROTECTED, f"{name} is encrypted")
        if info.file_size > limit:
            raise ConversionError(ErrorCode.CORRUPT_FILE, f"{name} is larger than allowed")
        try:
            with archive.open(info) as entry:
                data = entry.read(limit + 1)
        except (zipfile.BadZipFile, OSError, EOFError, ValueError, RuntimeError) as error:
            raise ConversionError(ErrorCode.CORRUPT_FILE, f"{name}: {error}") from error
        if len(data) > limit:  # the index lied about its size
            raise ConversionError(ErrorCode.CORRUPT_FILE, f"{name} is larger than allowed")
        return data

    def _check(self) -> None:
        names = self._zip().namelist()
        if len(names) != len(set(names)):  # readers disagree on which copy counts
            raise ConversionError(ErrorCode.CORRUPT_FILE, "an entry name appears twice")
        mime = self._read("mimetype", MAX_MIMETYPE_BYTES)
        if mime is None:
            raise ConversionError(ErrorCode.CORRUPT_FILE, "no mimetype entry")
        kind = mime.decode("ascii", errors="replace").strip()
        if kind != ODT_MIME:
            code = (
                ErrorCode.UNSUPPORTED_FORMAT
                if kind.startswith(ODF_MIME_PREFIX)
                else ErrorCode.CORRUPT_FILE
            )
            raise ConversionError(code, f"an OpenDocument of type {kind!r}, not a text document")
        manifest = self.part("META-INF/manifest.xml")
        if manifest is None:
            return
        for entry in manifest.elements("manifest:file-entry"):
            path = _entry_name(entry.get("manifest:full-path"))
            self._media_types[path] = entry.get("manifest:media-type")
            encrypted = entry.find("manifest:encryption-data") is not None
            if path in {"content.xml", "styles.xml"} and encrypted:
                raise ConversionError(ErrorCode.PASSWORD_PROTECTED, "the content is encrypted")

    def is_formula(self, part: str) -> bool:
        """Whether the manifest declares the object of ``part`` (``Object 1/content.xml``) a
        formula; used when the part itself cannot be read."""
        folder = part.rpartition("/")[0]
        return self._media_types.get(_entry_name(folder)) == FORMULA_MIME

    def part(self, name: str, *, max_bytes: int | None = None) -> Element | None:
        """The XML tree of an entry, ``None`` when it is not in the archive."""
        data = self._read(name, max_bytes)
        if data is None:
            return None
        try:
            return parse_part(data, self._limits)
        except XmlRefused as refused:
            raise ConversionError(ErrorCode.CORRUPT_FILE, f"{name}: {refused}") from None

    def content(self) -> Element:
        found = self.part("content.xml")
        if found is None:
            raise ConversionError(ErrorCode.CORRUPT_FILE, "no content.xml")
        return found

    def styles(self) -> Element | None:
        return self.part("styles.xml")
