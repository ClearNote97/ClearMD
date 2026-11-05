"""The images folder reaches only the converters that keep images (012): asking for it never
breaks the others (found in refactor R01: every .tex and .xlsx failed with "images" on)."""

from pathlib import Path
from typing import Any

from clearmd.backend.schemas.formats import FormatId, Strategy
from clearmd.backend.schemas.models import ConversionResult, Detection
from clearmd.backend.services.conversion.images import ImageSink
from clearmd.backend.services.worker.child import handle
from clearmd.backend.services.worker.protocol import Converted, ConvertRequest


class _Plain:
    """A converter that keeps no images: no ``images`` parameter (TeX, Excel)."""

    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        return ConversionResult("plain")


class _Pictures:
    """A converter that keeps them (PDF, Word, ODT)."""

    def __init__(self) -> None:
        self.sink: ImageSink | None = None

    def convert(
        self, source: Path, detection: Detection, target: Path, *, images: ImageSink | None = None
    ) -> ConversionResult:
        self.sink = images
        return ConversionResult("pictures")


class _Registry:
    def __init__(self, converter: Any) -> None:
        self.converter = converter

    def for_format(self, format_id: FormatId, strategy: Strategy = Strategy.FULL) -> Any:
        return self.converter

    def detect_content(self, path: Path) -> Detection | None:
        return None


def _request(images: str) -> ConvertRequest:
    return ConvertRequest("/docs/a.tex", "tex", "extension", "/out/a.md", images=images)


def test_a_converter_without_images_still_converts_with_the_folder_on() -> None:
    response = handle(_Registry(_Plain()), _request("a_images"), 10_000)
    assert isinstance(response, Converted) and response.markdown == "plain"


def test_a_converter_with_images_gets_the_folder() -> None:
    converter = _Pictures()
    response = handle(_Registry(converter), _request("a_images"), 10_000)
    assert isinstance(response, Converted) and converter.sink is not None
    assert converter.sink.folder == "a_images"


def test_with_the_folder_off_no_converter_gets_one() -> None:
    converter = _Pictures()
    handle(_Registry(converter), _request(""), 10_000)
    assert converter.sink is None
