"""Acceptance tests drive ``cli.main(argv)`` on copies of the fixtures, with the real worker."""

from dataclasses import replace
from pathlib import Path

import pytest
from support.worker_factories import REAL

from clearmd.backend.api import composition
from clearmd.backend.schemas.limits import Limits

ACCEPTANCE_TIME_PER_FILE = 60.0


@pytest.fixture(autouse=True)
def _guarded_real_worker(monkeypatch: pytest.MonkeyPatch) -> None:
    # The real converters, plus the network guard inside the worker process (AC-39).
    monkeypatch.setattr(composition, "REGISTRY_FACTORY", REAL)
    # A bug that sends a pathological file to the worker must fail a test, not hang the suite.
    real_limits = composition.default_limits

    def bounded_limits() -> Limits:
        limits = real_limits()
        return replace(limits, time_per_file=min(limits.time_per_file, ACCEPTANCE_TIME_PER_FILE))

    monkeypatch.setattr(composition, "default_limits", bounded_limits)


@pytest.fixture
def workdir(tmp_path: Path) -> Path:
    return tmp_path
