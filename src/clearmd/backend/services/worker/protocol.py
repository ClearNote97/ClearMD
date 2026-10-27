"""Messages between the supervisor and the worker process. Plain, picklable dataclasses."""

from dataclasses import dataclass

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


@dataclass(frozen=True)
class DetectRequest:
    source: str


@dataclass(frozen=True)
class Detected:
    format: str | None


@dataclass(frozen=True)
class Converted:
    markdown: str
    notes: tuple[ConversionNote, ...] = ()


@dataclass(frozen=True)
class Failed:
    code: str
    detail: str


type Request = ConvertRequest | DetectRequest | None  # None asks the worker to exit
type Response = Converted | Detected | Failed
