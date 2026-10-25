"""Resource limits for untrusted documents and the cost weights of the queue (ADR-0015).

Initial values; the benchmark of feature 001 (T07) replaces them with measured ones.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from clearmd.backend.schemas.formats import FormatId

MIB = 1024**2
GIB = 1024**3

# openpyxl holds many times an xlsx's size in memory; pdfminer is slow per page.
DEFAULT_WEIGHTS: Mapping[FormatId, float] = MappingProxyType(
    {FormatId.XLSX: 20.0, FormatId.PDF: 4.0}
)


@dataclass(frozen=True)
class Limits:
    max_file_size: int = 250 * MIB
    max_uncompressed: int = 1 * GIB
    max_ratio: float = 100.0
    time_per_file: float = 600.0
    # The composition root lowers it to half of the machine's RAM when that is smaller.
    worker_memory: int = 4 * GIB
    weights: Mapping[FormatId, float] = field(default_factory=lambda: DEFAULT_WEIGHTS)

    def weight(self, format_id: FormatId) -> float:
        return self.weights.get(format_id, 1.0)
