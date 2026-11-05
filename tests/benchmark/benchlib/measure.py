"""Measurement, parent side: spawn, sample memory, stop and collect the rows."""

import json
import multiprocessing
import random
import statistics
import time
import zipfile
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import psutil

from benchlib.cases import Case
from benchlib.child import _measure_child, _startup_child
from benchlib.common import MIB, SAMPLE_SECONDS, SEED


def _run_child(
    target: Callable[..., None], args: tuple[Any, ...], *, memory_cap: int, timeout: float
) -> dict[str, Any]:
    context = multiprocessing.get_context("spawn")
    parent_end, child_end = context.Pipe()
    process = context.Process(target=target, args=(child_end, *args), daemon=True)
    started = time.perf_counter()
    process.start()
    child_end.close()
    sampled_peak = 0
    try:
        while True:
            if parent_end.poll(SAMPLE_SECONDS):
                result: dict[str, Any] = parent_end.recv()
                result["sampled_peak_mib"] = sampled_peak / MIB
                result["wall_s"] = time.perf_counter() - started
                return result
            try:
                rss = psutil.Process(process.pid).memory_info().rss
            except psutil.Error:
                rss = 0
            sampled_peak = max(sampled_peak, rss)
            if rss > memory_cap:
                return {"ok": False, "error": f"stopped above the {memory_cap // MIB} MiB cap"}
            if time.perf_counter() - started > timeout:
                return {"ok": False, "error": f"stopped after {timeout:g} s"}
            if not process.is_alive():
                return {"ok": False, "error": f"process exited with code {process.exitcode}"}
    finally:
        if process.is_alive():
            process.kill()
        process.join()


def zip_stats(path: Path) -> dict[str, float] | None:
    if not zipfile.is_zipfile(path):
        return None
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
    uncompressed = sum(info.file_size for info in infos)
    worst = max(
        (info.file_size / info.compress_size for info in infos if info.compress_size), default=0
    )
    return {
        "uncompressed_mib": uncompressed / MIB,
        "total_ratio": uncompressed / path.stat().st_size,
        "worst_entry_ratio": worst,
    }


@dataclass
class Row:
    kind: str
    size_mib: float
    file_mib: float
    result: dict[str, Any]
    archive: dict[str, float] | None


def run(
    cases: list[Case],
    workdir: Path,
    *,
    memory_cap: int,
    timeout: float,
    slow_after: float,
    log: Callable[[str], None] = print,
) -> list[Row]:
    rows: list[Row] = []
    for case in cases:
        rng = random.Random(SEED)
        for size_mib in case.sizes_mib:
            path = workdir / f"{case.kind}_{size_mib:g}{case.extension}"
            case.build(path, int(size_mib * MIB), rng)
            result = _run_child(
                _measure_child,
                (str(path), case.extension, case.engine),
                memory_cap=memory_cap,
                timeout=timeout,
            )
            row = Row(case.kind, size_mib, path.stat().st_size / MIB, result, zip_stats(path))
            rows.append(row)
            log(json.dumps(asdict(row)))
            path.unlink()
            if not result.get("ok") or result.get("seconds", 0) > slow_after:
                log(f"# {case.kind}: larger sizes skipped after {size_mib:g} MiB")
                break
    return rows


def startup(repetitions: int, *, memory_cap: int, timeout: float) -> dict[str, float]:
    runs = [
        _run_child(_startup_child, (), memory_cap=memory_cap, timeout=timeout)
        for _ in range(repetitions)
    ]
    return {key: statistics.median(run[key] for run in runs) for key in runs[0] if key != "error"}
