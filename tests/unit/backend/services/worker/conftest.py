"""A worker runner on the fake worker, closed after each test."""

from collections.abc import Iterator

import pytest
from support.supervisor_cases import TIGHT
from support.worker_factories import FAKE

from clearmd.backend.services.worker.supervisor import WorkerRunner


@pytest.fixture
def runner() -> Iterator[WorkerRunner]:
    worker = WorkerRunner(FAKE, TIGHT)
    yield worker
    worker.close()
