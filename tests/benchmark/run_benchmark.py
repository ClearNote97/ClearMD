"""Benchmarks of features 001, 002 and 003: conversion time and peak memory per format.

Run inside the container (takes several minutes; results to a JSON file):

    uv run python tests/benchmark/run_benchmark.py --out docs/benchmarks/001-results.json
    uv run python tests/benchmark/run_benchmark.py --only tex tex_macros \
        --out docs/benchmarks/002-results.json
    uv run python tests/benchmark/run_benchmark.py --only odt --out docs/benchmarks/003-results.json
    uv run python tests/benchmark/run_benchmark.py --only html_article \\
        --out docs/benchmarks/004-results.json

Every measurement runs its converter (markitdown, or ClearMD's own for ``.tex`` and ``.odt``) in a
fresh *spawn* process, like the worker of ADR-0015. The
parent samples that process's memory and stops it above ``--memory-cap-mib`` so the benchmark never
exhausts the machine. Generated documents are pseudo-random text with a fixed seed: reproducible,
and compressing like real prose (about 3-4:1) instead of like repeated filler.
"""

import argparse
import json
import platform
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

import psutil
from benchlib.cases import CASES
from benchlib.common import MIB
from benchlib.measure import run, startup


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ClearMD benchmarks (features 001 and 002)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--memory-cap-mib", type=int, default=2048)
    parser.add_argument("--timeout", type=float, default=900)
    parser.add_argument("--slow-after", type=float, default=300)
    parser.add_argument("--only", nargs="*", help="kinds to run (default: all)")
    args = parser.parse_args(argv)
    cap = args.memory_cap_mib * MIB
    cases = [case for case in CASES if not args.only or case.kind in args.only]
    with tempfile.TemporaryDirectory(prefix="clearmd-bench-") as tmp:
        measured_startup = startup(3, memory_cap=cap, timeout=args.timeout)
        print(json.dumps({"startup": measured_startup}))
        rows = run(
            cases, Path(tmp), memory_cap=cap, timeout=args.timeout, slow_after=args.slow_after
        )
    machine = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cpus": psutil.cpu_count(),
        "ram_mib": psutil.virtual_memory().total // MIB,
        "memory_cap_mib": args.memory_cap_mib,
    }
    payload = {"machine": machine, "startup": measured_startup, "rows": [asdict(r) for r in rows]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
