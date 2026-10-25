"""The composition root: the only place that builds services (ADR-0014)."""

import psutil

from clearmd.backend.schemas.limits import Limits
from clearmd.backend.services.clock import SystemClock
from clearmd.backend.services.detection.chain import ChainDetector
from clearmd.backend.services.detection.content_policy import DocumentsOnlyWithExtension
from clearmd.backend.services.detection.extension import ExtensionDetector
from clearmd.backend.services.worker.supervisor import REAL_REGISTRY, WorkerRunner

# Read at call time, so the tests can point the worker at a guarded registry (AC-39).
REGISTRY_FACTORY = REAL_REGISTRY
MAX_WORKER_MEMORY = Limits().worker_memory


def worker_memory_limit(total_ram: int) -> int:
    """Half of the machine's RAM, at most 4 GiB (ADR-0015)."""
    return min(total_ram // 2, MAX_WORKER_MEMORY)


def default_limits() -> Limits:
    return Limits(worker_memory=worker_memory_limit(psutil.virtual_memory().total))


def build_detector(worker: WorkerRunner) -> ChainDetector:
    """Extension first (free); content only when the extension says nothing (in the worker)."""
    return ChainDetector(ExtensionDetector(), DocumentsOnlyWithExtension(worker))


def build_runner(limits: Limits) -> WorkerRunner:
    return WorkerRunner(REGISTRY_FACTORY, limits)


def build_clock() -> SystemClock:
    return SystemClock()
