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


# MiB of worker memory per MiB of size (same size as the cost), from the peaks of benchmark 001.
MEMORY_PER_MIB: Mapping[FormatId, float] = MappingProxyType(
    {
        FormatId.XLSX: 25.7,
        FormatId.CSV: 13.7,
        FormatId.DOCX: 11.7,
        FormatId.PDF: 8.7,
        FormatId.HTML: 7.0,
        FormatId.PPTX: 6.7,
        FormatId.TXT: 3.9,
        FormatId.IPYNB: 3.7,
        FormatId.EPUB: 3.2,
    }
)


@dataclass(frozen=True)
class Limits:
    max_file_size: int = 250 * MIB
    max_uncompressed: int = 1 * GIB
    # Uncompressed size over the whole file's size; real documents measured 1-5, the bomb ~340.
    max_ratio: float = 100.0
    # Entries a ZIP-based document may declare: real ones have tens to a few thousand.
    max_zip_entries: int = 50_000
    time_per_file: float = 600.0
    # The composition root lowers it to half of the machine's RAM when that is smaller.
    worker_memory: int = 4 * GIB
    worker_startup_seconds: float = 0.7
    # Characters of Markdown a worker may send back (a 250 MiB CSV gives ~290 M).
    max_result_chars: int = 512 * 1024**2
    # Python + markitdown + magika, resident before any file (benchmark 001).
    worker_base_memory: int = 160 * MIB
    weights: Mapping[FormatId, float] = field(default_factory=lambda: SECONDS_PER_MIB)
    memory_per_mib: Mapping[FormatId, float] = field(default_factory=lambda: MEMORY_PER_MIB)

    def weight(self, format_id: FormatId) -> float:
        return self.weights[format_id]

    def estimated_seconds(self, format_id: FormatId, size: int) -> float:
        return size / MIB * self.weight(format_id)

    def estimated_memory(self, format_id: FormatId, size: int) -> int:
        return self.worker_base_memory + round(size * self.memory_per_mib[format_id])
