"""Acceptance tests drive ``cli.main(argv)`` on copies of the fixtures, with the real worker."""

from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from support.gui_close import shut
from support.ttk_acceptance import pump
from support.worker_factories import REAL

from clearmd.backend.api import composition
from clearmd.backend.schemas.limits import Limits
from clearmd.frontend.ttk import TtkApp

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


@pytest.fixture
def window(display: str) -> Iterator[Callable[..., TtkApp]]:
    """Opens a ttk window on a backend and closes every one at the end of the test."""
    opened: list[TtkApp] = []

    def make(backend: Any) -> TtkApp:
        app = TtkApp(backend)
        app.start()
        pump(app, seconds=0.1)
        opened.append(app)
        return app

    yield make
    for app in opened:
        try:
            shut(app)
        except Exception:  # noqa: BLE001 -- already closed by the test
            pass
