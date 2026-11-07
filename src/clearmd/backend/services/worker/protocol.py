"""Messages between the supervisor and the worker process. Plain, picklable dataclasses."""

from dataclasses import dataclass

from clearmd.backend.schemas.models import ExtractedImage
from clearmd.backend.schemas.notes import ConversionNote


@dataclass(frozen=True)
class Ready:
    """Sent once by the worker when its converters are loaded; time limits start after it."""


@dataclass(frozen=True)
class ConvertRequest:
    source: str
    format: str
    method: str
    target: str  # where the Markdown will be written: links to images start there
    strategy: str = "full"  # Strategy: HTML may be converted to its article only (004)
    images: str = ""  # the images folder's name; empty: images left out (012)


@dataclass(frozen=True)
class DetectRequest:
    source: str


@dataclass(frozen=True)
class CountPagesRequest:
    """How many pages a PDF has (Split, feature 023)."""

    source: str


@dataclass(frozen=True)
class CutRequest:
    """A new PDF with the pages ``first``..``last`` (1-based) of ``source`` (feature 023)."""

    source: str
    first: int
    last: int


@dataclass(frozen=True)
class WordsRequest:
    """The words on each page of a PDF (Split by words, feature 024)."""

    source: str


@dataclass(frozen=True)
class MarkdownCutRequest:
    """A Markdown file cut at its headings (feature 024): ``cut`` is "parts" or "words"."""

    source: str
    cut: str
    size: int


@dataclass(frozen=True)
class Words:
    per_page: tuple[int, ...]


@dataclass(frozen=True)
class MarkdownParts:
    parts: tuple[str, ...]
    over: tuple[int, ...] = ()  # the parts (1-based) larger than the size


@dataclass(frozen=True)
class Counted:
    pages: int


@dataclass(frozen=True)
class CutDone:
    data: bytes


@dataclass(frozen=True)
class Detected:
    format: str | None


@dataclass(frozen=True)
class Converted:
    markdown: str
    notes: tuple[ConversionNote, ...] = ()
    images: tuple[ExtractedImage, ...] = ()


@dataclass(frozen=True)
class Failed:
    code: str
    detail: str


type PageJob = CountPagesRequest | CutRequest | WordsRequest | MarkdownCutRequest
type Job = ConvertRequest | DetectRequest | PageJob
type Request = Job | None  # None asks the worker to exit
type Response = Converted | Detected | Counted | CutDone | Words | MarkdownParts | Failed
