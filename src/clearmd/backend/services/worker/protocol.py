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
class ReadTextRequest:
    """A Markdown file's text, as it is (Merge, feature 026)."""

    source: str


@dataclass(frozen=True)
class MergePdfRequest:
    """One PDF with every page of ``sources``, whole and in order (Merge, feature 026)."""

    sources: tuple[str, ...]


@dataclass(frozen=True)
class TextCutRequest:
    """A text or CSV file cut between lines or rows (feature 027): ``kind`` "txt" or "csv"."""

    source: str
    kind: str
    cut: str
    size: int


@dataclass(frozen=True)
class XlsxCutRequest:
    """An Excel workbook cut into ``parts`` of whole sheets (feature 027)."""

    source: str
    parts: int


@dataclass(frozen=True)
class FileParts:
    data: tuple[bytes, ...]


@dataclass(frozen=True)
class TextRead:
    text: str


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


@dataclass(frozen=True)
class Progress:
    """How far the current job has got (audit 2026-11-08, 3B): sent before its answer, any
    number of times, at most once a second."""

    done: int
    total: int


type PageJob = (
    CountPagesRequest
    | CutRequest
    | WordsRequest
    | MarkdownCutRequest
    | ReadTextRequest
    | MergePdfRequest
    | TextCutRequest
    | XlsxCutRequest
)
type Job = ConvertRequest | DetectRequest | PageJob
type Request = Job | None  # None asks the worker to exit
type Response = (
    Converted | Detected | Counted | CutDone | Words | MarkdownParts | TextRead | FileParts | Failed
)
