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


def test_xlsx_weighs_more_than_pdf_and_pdf_more_than_the_rest() -> None:
    limits = Limits()
    assert limits.weight(FormatId.XLSX) > limits.weight(FormatId.PDF) > limits.weight(FormatId.TXT)
    assert limits.weight(FormatId.TXT) == 1


def test_limits_are_immutable() -> None:
    limits = Limits()
    with pytest.raises(dataclasses.FrozenInstanceError):
        limits.time_per_file = 1  # type: ignore[misc]
    with pytest.raises(TypeError):
        limits.weights[FormatId.PDF] = 1  # type: ignore[index]


def test_limits_can_be_tightened_for_tests() -> None:
    assert Limits(time_per_file=0.5).time_per_file == 0.5
