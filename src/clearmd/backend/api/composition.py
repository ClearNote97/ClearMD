"""The composition root: the only place that builds services (ADR-0014)."""

from importlib.metadata import version
from typing import TYPE_CHECKING

import psutil

from clearmd.backend.schemas.limits import Limits
from clearmd.backend.services.clock import SystemClock
from clearmd.backend.services.detection.chain import ChainDetector
from clearmd.backend.services.detection.content_policy import ExtensionlessOnly
from clearmd.backend.services.detection.extension import ExtensionDetector
from clearmd.backend.services.summary.writer import MarkdownSummaryWriter
from clearmd.backend.services.worker.page_runner import PageRunner
from clearmd.backend.services.worker.supervisor import REAL_REGISTRY, WorkerRunner
from clearmd.i18n import load_catalog

if TYPE_CHECKING:
    from clearmd.backend.services.summary.pdf_report import PdfReport

# Read at call time, so the tests can point the worker at a guarded registry (AC-39).
REGISTRY_FACTORY = REAL_REGISTRY
MAX_WORKER_MEMORY = Limits().worker_memory


def worker_memory_limit(total_ram: int) -> int:
    """Half of the machine's RAM, at most 4 GiB (ADR-0015)."""
    return min(total_ram // 2, MAX_WORKER_MEMORY)


def default_limits() -> Limits:
    return Limits(worker_memory=worker_memory_limit(psutil.virtual_memory().total))


def build_detector(worker: WorkerRunner) -> ChainDetector:
    """Extension first (free); content, in the worker, only for files without an extension."""
    return ChainDetector(ExtensionDetector(), ExtensionlessOnly(worker))


def build_runner(limits: Limits) -> WorkerRunner:
    return WorkerRunner(REGISTRY_FACTORY, limits)


def build_page_runner(runner: WorkerRunner) -> PageRunner:
    """Split's page jobs, on the same worker as the conversions (ADR-0044)."""
    return PageRunner(runner)


def build_clock() -> SystemClock:
    return SystemClock()


def build_summary_writer(language: str) -> MarkdownSummaryWriter:
    return MarkdownSummaryWriter(load_catalog(language), version=version("clearmd"))


def build_pdf_report(language: str) -> "PdfReport":
    """Imported when a PDF summary is asked for: PDFium is not loaded at start-up (B2-04)."""
    from clearmd.backend.services.summary.pdf_report import PdfReport  # noqa: PLC0415

    return PdfReport(load_catalog(language), version=version("clearmd"))
