import dataclasses

import pytest

from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.limits import GIB, MIB, Limits


def test_defaults_follow_adr_0015() -> None:
    limits = Limits()
    assert limits.max_file_size == 250 * MIB
    assert limits.max_uncompressed == 1 * GIB
    assert limits.max_ratio == 100
    assert limits.time_per_file == 600
    assert limits.worker_memory == 4 * GIB


def test_every_format_has_a_measured_speed() -> None:
    assert set(Limits().weights) == set(FormatId)


def test_weights_are_seconds_per_mib_from_the_benchmark() -> None:
    limits = Limits()
    # docs/benchmarks/001-conversion-limits.md: PDF is the slowest, plain text the fastest.
    assert limits.weight(FormatId.PDF) == max(limits.weights.values())
    assert limits.weight(FormatId.TXT) == min(limits.weights.values())
    assert 20 < limits.weight(FormatId.PDF) < 40


def test_estimated_seconds_of_a_file() -> None:
    limits = Limits()
    assert limits.estimated_seconds(FormatId.PDF, 2 * MIB) == 2 * limits.weight(FormatId.PDF)


def test_worker_start_up_was_measured() -> None:
    assert 0 < Limits().worker_startup_seconds < 2


def test_limits_are_immutable() -> None:
    limits = Limits()
    with pytest.raises(dataclasses.FrozenInstanceError):
        limits.time_per_file = 1  # type: ignore[misc]
    with pytest.raises(TypeError):
        limits.weights[FormatId.PDF] = 1  # type: ignore[index]


def test_limits_can_be_tightened_for_tests() -> None:
    assert Limits(time_per_file=0.5).time_per_file == 0.5
