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
    # The benchmarks: TeX (pylatexenc) is the slowest since PDF is read by PDFium (ADR-0030,
    # about 5 s per MiB of text); plain text the fastest.
    assert limits.weight(FormatId.TEX) == max(limits.weights.values())
    assert limits.weight(FormatId.TXT) == min(limits.weights.values())
    assert 4 < limits.weight(FormatId.PDF) < 10


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


def test_estimated_memory_adds_the_worker_base_and_the_format_factor() -> None:
    limits = Limits()
    expected = limits.worker_base_memory + 10 * limits.memory_per_mib[FormatId.XLSX] * MIB
    assert limits.estimated_memory(FormatId.XLSX, 10 * MIB) == expected


def test_a_60_mb_xlsx_does_not_fit_and_a_10_mb_pdf_does() -> None:
    limits = Limits()
    # 60 MB of xlsx is ~276 MiB of XML inside (ratio 4.6, benchmark 001).
    assert limits.estimated_memory(FormatId.XLSX, 276 * MIB) > limits.worker_memory
    assert limits.estimated_memory(FormatId.PDF, 10 * MIB) < limits.worker_memory


def test_every_format_has_a_memory_factor() -> None:
    assert set(Limits().memory_per_mib) == set(FormatId)
