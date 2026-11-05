"""The page's pictures as lines at their place, kept by the image sink (feature 012)."""

import ctypes
import io

import pypdfium2 as pdfium
import pypdfium2.raw as raw

from clearmd.backend.services.conversion.images import ImageSink
from clearmd.backend.services.conversion.pdf.model import Line
from clearmd.backend.services.conversion.pdf.pdfium.image_objects import image_objects

MAX_PICTURE_PIXELS = 40_000_000  # a picture's own pixels, read before it is decoded


def pictures(document: object, page: object, sink: ImageSink, budget: list[int]) -> list[Line]:
    """The page's pictures as lines at their place, each kept by the sink (012). Each is decoded
    at its own size, checked before (never rendered at the size it is drawn: a 2 x 2 picture
    drawn 12,000 points wide, review of 012), within the document's budget of pixels; those
    inside a form object are found too, placed where the form stands."""
    lines: list[Line] = []
    for obj, box in image_objects(page):
        data = _picture_png(obj, budget)
        link = sink.add(data) if data is not None else None
        if data is None:
            sink.left_out += 1
        if link is not None:
            lines.append(Line("", 0.0, False, box[3], box[1], image=link))
    return lines


def _picture_png(obj: object, budget: list[int]) -> bytes | None:
    """The picture at its own size, as PNG; None when it is too large or cannot be decoded."""
    width, height = ctypes.c_uint(), ctypes.c_uint()
    if not raw.FPDFImageObj_GetImagePixelSize(obj, ctypes.byref(width), ctypes.byref(height)):
        return None
    pixels = width.value * height.value
    if not 0 < pixels <= MAX_PICTURE_PIXELS or pixels > budget[0]:
        return None
    budget[0] -= pixels
    bitmap = raw.FPDFImageObj_GetBitmap(obj)
    if not bitmap:
        return None
    picture = pdfium.PdfBitmap.from_raw(bitmap)
    picture.warn_on_close = False  # closed only once the PNG is written from a copy of it
    try:
        data = io.BytesIO()
        picture.to_pil().convert("RGB").save(data, "PNG")
        return data.getvalue()
    except (ValueError, OSError, MemoryError):
        return None
    finally:
        picture.close()


def placed(lines: list[Line], pictures: list[Line]) -> list[Line]:
    """Each picture before the first line below its top: the reading order of the page."""
    for picture in sorted(pictures, key=lambda line: -line.top):
        at = next((i for i, line in enumerate(lines) if line.top < picture.top), len(lines))
        lines.insert(at, picture)
    return lines
