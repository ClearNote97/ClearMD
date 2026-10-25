"""Detection by content with magika. Imported only inside the worker process (AC-19).

The label table was verified against magika 1.0.3 on the fixtures (T10). magika applies its own
confidence thresholds: a low-confidence result comes back as a generic label (``unknown``), which is
not in the table and therefore means "unsupported".
"""

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

import magika

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod

LABELS: Mapping[str, FormatId] = MappingProxyType(
    {
        "pdf": FormatId.PDF,
        "docx": FormatId.DOCX,
        "pptx": FormatId.PPTX,
        "xlsx": FormatId.XLSX,
        "html": FormatId.HTML,
        "csv": FormatId.CSV,
        "epub": FormatId.EPUB,
        "ipynb": FormatId.IPYNB,
        "txt": FormatId.TXT,
    }
)


class MagikaDetector:
    """One magika model per process, loaded on first use (~no memory, benchmark 001)."""

    def __init__(self) -> None:
        self._magika: magika.Magika | None = None

    def detect(self, path: Path) -> Detection | None:
        if self._magika is None:
            self._magika = magika.Magika()
        label = str(self._magika.identify_path(path).output.label)
        format_id = LABELS.get(label)
        return Detection(format_id, DetectionMethod.CONTENT) if format_id is not None else None
