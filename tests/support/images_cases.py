"""Picture builders shared by the image tests (feature 012)."""

import io

from PIL import Image

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod


def png(colour: str = "red", size: tuple[int, int] = (60, 40)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, colour).save(buffer, "PNG")
    return buffer.getvalue()


def detection(format_id: FormatId) -> Detection:
    return Detection(format_id, DetectionMethod.EXTENSION)
