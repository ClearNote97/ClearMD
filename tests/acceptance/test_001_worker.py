"""Feature 001 — the worker process: memory limit, crashes and the blocked network."""

import random
from dataclasses import replace
from pathlib import Path

import pytest
from build_fixtures import MARKERS
from run_benchmark import SEED, make_csv
from support import put
from support.batch_cli import _summary
from support.worker_factories import FAKE

from clearmd.backend.api import composition
from clearmd.backend.schemas.formats import FormatId
from clearmd.frontend.cli import main


def test_ac_24_a_worker_over_the_memory_limit_is_stopped_and_replaced(
    workdir: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # A 12 MiB CSV peaks near 280 MiB (markitdown's table); Excel no longer does since ClearMD
    # reads it itself (feature 010: ~40 MiB for 2 MiB).
    make_csv(workdir / "sales.csv", 12 * 1024**2, random.Random(SEED))
    after = put(workdir, "sample.txt", "zz_after.txt")
    # The plan must not skip it (AC-42), so its estimate is zeroed; the real use is not.
    base = composition.default_limits()
    limits = replace(
        base,
        worker_memory=230 * 1024**2,
        memory_per_mib={**base.memory_per_mib, FormatId.CSV: 0.0},
        weights={**base.weights, FormatId.CSV: 0.0},  # convert it first
    )
    monkeypatch.setattr(composition, "default_limits", lambda: limits)
    assert main([str(workdir / "sales.csv"), str(after)]) == 1
    err = capsys.readouterr().err
    assert "⏹ Stopped: sales.csv — Exceeded the memory limit" in err
    assert "close other programs" in err
    assert (workdir / "ClearMD_Output" / "OutputMD" / "zz_after.md").is_file()  # new worker


def test_ac_25_a_crashing_worker_fails_that_file_and_the_batch_goes_on(
    workdir: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(composition, "REGISTRY_FACTORY", FAKE)  # its "crash" file kills the worker
    crash = put(workdir, "sample.txt", "crash.txt")
    after = put(workdir, "sample.txt", "zz_after.txt")
    assert main([str(crash), str(after)]) == 1
    assert "crash.txt — The converter stopped unexpectedly" in capsys.readouterr().err
    assert (workdir / "ClearMD_Output" / "OutputMD" / "zz_after.md").is_file()


def test_ac_39_every_format_converts_with_the_network_blocked_in_the_worker(
    workdir: Path,
) -> None:
    samples = [put(workdir, name) for name in sorted(MARKERS) if name.startswith("sample.")]
    assert main([*map(str, samples), "--quiet"]) == 0  # the REAL factory guards the worker


def test_ac_39_a_converter_that_tries_the_network_is_stopped(
    workdir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(composition, "REGISTRY_FACTORY", FAKE)  # "network" opens a socket
    source = put(workdir, "sample.txt", "network.txt")
    assert main([str(source), "--quiet"]) == 1
    assert "NetworkBlockedError" in _summary(workdir)
