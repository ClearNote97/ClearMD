"""Messages between the supervisor and the worker process. Plain, picklable dataclasses."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConvertRequest:
    source: str
    format: str
    method: str


@dataclass(frozen=True)
class Converted:
    markdown: str


@dataclass(frozen=True)
class Failed:
    code: str
    detail: str


type Request = ConvertRequest | None  # None asks the worker to exit
type Response = Converted | Failed
