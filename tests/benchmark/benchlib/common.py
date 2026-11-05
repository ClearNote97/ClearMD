"""Constants and helpers shared by the benchmark's generators."""

import random
import zipfile
from collections.abc import Callable
from pathlib import Path

MIB = 1024**2
SEED = 2026
SAMPLE_SECONDS = 0.05

_SYLLABLES = [
    "ka",
    "lo",
    "mi",
    "ne",
    "ru",
    "ta",
    "so",
    "vi",
    "de",
    "pa",
    "ri",
    "zo",
    "fe",
    "gu",
    "bi",
]


def _words(rng: random.Random, count: int) -> str:
    return " ".join(
        "".join(rng.choice(_SYLLABLES) for _ in range(rng.randint(1, 4))) for _ in range(count)
    )


def _line(rng: random.Random) -> str:
    return _words(rng, rng.randint(8, 14))


def _zip_size(archive: zipfile.ZipFile) -> int:
    assert archive.fp is not None
    return archive.fp.tell()


def _calibrated(
    build: Callable[[Path, int, random.Random], None],
    probe_units: int,
    path: Path,
    size: int,
    rng: random.Random,
) -> None:
    """For formats whose size is only known after saving: build small, scale up linearly."""
    build(path, probe_units, random.Random(SEED))
    units = max(1, round(probe_units * size / path.stat().st_size))
    build(path, units, rng)
