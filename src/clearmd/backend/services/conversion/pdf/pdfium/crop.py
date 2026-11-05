"""An equation as it looks on the page: its place rendered and trimmed to the ink (feature 013)."""

import io

import pypdfium2 as pdfium
import pypdfium2.raw as raw
from PIL import Image

from clearmd.backend.services.conversion.images import ImageSink
from clearmd.backend.services.conversion.pdf.model import Line
from clearmd.backend.services.conversion.pdf.pdfium.document import finite
from clearmd.backend.services.conversion.pdf.pdfium.pictures import MAX_PICTURE_PIXELS

CROP_SCALE = 2.0  # an equation's picture: 144 dots per inch
CROP_PAD = 3.0  # points around it
MAX_PAGE_POINTS = 14_400.0  # PDF's largest page side (200 inches)
INK_LEVEL = 160  # a grey this dark is ink
APART_PIXELS = 6  # a blank this tall (at 144 dpi) parts the equation from a neighbour's sliver
TRIM_MARGIN = 6  # pixels of white kept around the ink


def pictured(page: object, line: Line, images: ImageSink, budget: list[int]) -> Line:
    """An equation, as it looks on the page, when the images folder is on (013): within the
    document's pixels and crops (each renders the page; review of 013), else its text."""
    if not line.equation or line.latex or budget[1] <= 0:
        return line
    budget[1] -= 1
    data = cropped(page, line, budget)
    link = images.add(data) if data is not None else None
    if link is None:
        return line
    return Line("", line.size, False, line.top, line.bottom, image=link, left=line.left)


def cropped(page: object, line: Line, budget: list[int]) -> bytes | None:
    """The equation's place on the page, rendered: a PNG, or None (a turned or outsized page, a
    crop past the budget, nothing drawn there, a failure: its text is written instead)."""
    if raw.FPDFPage_GetRotation(page) != 0:
        return None
    height = finite(raw.FPDF_GetPageHeightF(page))
    width = finite(raw.FPDF_GetPageWidthF(page))
    if not (0 < width <= MAX_PAGE_POINTS and 0 < height <= MAX_PAGE_POINTS):
        return None  # past PDF's own limit: an offset ctypes cannot hold (review of 013)
    left, right = max(line.left - CROP_PAD, 0.0), min(line.right + CROP_PAD, width)
    bottom, top = max(line.bottom - CROP_PAD, 0.0), min(line.top + CROP_PAD, height)
    pixels_x, pixels_y = round((right - left) * CROP_SCALE), round((top - bottom) * CROP_SCALE)
    pixels = pixels_x * pixels_y
    if not 0 < pixels <= min(MAX_PICTURE_PIXELS, budget[0]):
        return None
    budget[0] -= pixels
    bitmap = raw.FPDFBitmap_Create(pixels_x, pixels_y, 0)
    if not bitmap:
        return None
    picture = pdfium.PdfBitmap.from_raw(bitmap)
    picture.warn_on_close = False  # closed only once the PNG is written from a copy of it
    try:
        raw.FPDFBitmap_FillRect(bitmap, 0, 0, pixels_x, pixels_y, 0xFFFFFFFF)
        raw.FPDF_RenderPageBitmap(
            bitmap,
            page,
            round(-left * CROP_SCALE),
            round(-(height - top) * CROP_SCALE),
            round(width * CROP_SCALE),
            round(height * CROP_SCALE),
            0,
            raw.FPDF_ANNOT,
        )
        trimmed = _trimmed(picture.to_pil().convert("RGB"))
        if trimmed is None:
            return None
        data = io.BytesIO()
        trimmed.save(data, "PNG")
        return data.getvalue()
    except (ValueError, OSError, MemoryError):
        return None
    finally:
        picture.close()


def _trimmed(image: Image.Image) -> Image.Image | None:
    """The equation's ink, a margin around it: a sliver of the line above or below, at the edge
    and apart from it, goes (a font's boxes reach far past its letters)."""
    ink = image.convert("L").point(lambda value: 255 if value < INK_LEVEL else 0)
    width, height = ink.size
    rows = [ink.crop((0, y, width, y + 1)).getbbox() is not None for y in range(height)]
    bands: list[list[int]] = []
    for y, inked in enumerate(rows):
        if inked and bands and y - bands[-1][1] <= APART_PIXELS:
            bands[-1][1] = y
        elif inked:
            bands.append([y, y])
    if len(bands) > 1 and bands[-1][1] == height - 1:
        bands.pop()  # the line below's top
    if len(bands) > 1 and bands[0][0] == 0:
        bands.pop(0)  # the line above's foot
    if not bands:
        return None  # no ink: nothing drawn there, the text says more
    box = ink.crop((0, bands[0][0], width, bands[-1][1] + 1)).getbbox()
    if box is None:
        return None
    left, right = max(box[0] - TRIM_MARGIN, 0), min(box[2] + TRIM_MARGIN, width)
    top, bottom = max(bands[0][0] - TRIM_MARGIN, 0), min(bands[-1][1] + 1 + TRIM_MARGIN, height)
    return image.crop((left, top, right, bottom))
