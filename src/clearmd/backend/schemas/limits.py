"""Resource limits for untrusted documents and the speed of each format (ADR-0015).

Values measured by the benchmark of feature 001: ``docs/benchmarks/001-conversion-limits.md``.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from clearmd.backend.schemas.formats import FormatId

MIB = 1024**2
GIB = 1024**3

# Seconds of conversion per MiB, so a file's cost is its estimated conversion time. For ZIP-based
# formats the MiB are the uncompressed text parts (XML/XHTML), not images: a docx of photos is fast.
SECONDS_PER_MIB: Mapping[FormatId, float] = MappingProxyType(
    {
        FormatId.PDF: 31.0,
        FormatId.XLSX: 1.5,
        FormatId.PPTX: 1.2,
        FormatId.DOCX: 0.6,
        FormatId.HTML: 0.2,
        FormatId.CSV: 0.15,
        FormatId.EPUB: 0.15,
        FormatId.IPYNB: 0.03,
        FormatId.TXT: 0.03,
    }
)


@dataclass(frozen=True)
class Limits:
    max_file_size: int = 250 * MIB
    max_uncompressed: int = 1 * GIB
    # Uncompressed size over the whole file's size; real documents measured 1-5, the bomb ~340.
    max_ratio: float = 100.0
    time_per_file: float = 600.0
    # The composition root lowers it to half of the machine's RAM when that is smaller.
    worker_memory: int = 4 * GIB
    worker_startup_seconds: float = 0.7
    weights: Mapping[FormatId, float] = field(default_factory=lambda: SECONDS_PER_MIB)

    def weight(self, format_id: FormatId) -> float:
        return self.weights[format_id]

    def estimated_seconds(self, format_id: FormatId, size: int) -> float:
        return size / MIB * self.weight(format_id)
