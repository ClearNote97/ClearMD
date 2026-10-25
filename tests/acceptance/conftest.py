"""Acceptance tests drive ``cli.main(argv)`` on copies of the fixtures, with the real worker."""

from pathlib import Path

import pytest
from support.worker_factories import REAL

from clearmd.backend.api import composition


@pytest.fixture(autouse=True)
def _guarded_real_worker(monkeypatch: pytest.MonkeyPatch) -> None:
    # The real converters, plus the network guard inside the worker process (AC-39).
    monkeypatch.setattr(composition, "REGISTRY_FACTORY", REAL)


@pytest.fixture
def workdir(tmp_path: Path) -> Path:
    return tmp_path
