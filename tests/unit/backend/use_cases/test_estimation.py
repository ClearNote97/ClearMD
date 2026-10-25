import pytest

from clearmd.backend.use_cases.estimation import TimeLeft

OVERHEAD = TimeLeft.PER_FILE_OVERHEAD


def test_before_any_file_the_estimate_is_the_costs_plus_start_up() -> None:
    estimate = TimeLeft(startup_seconds=0.7)
    assert estimate.seconds_left([10.0, 20.0]) == pytest.approx(0.7 + 30 + 2 * OVERHEAD)


def test_measured_speed_corrects_the_estimate() -> None:
    estimate = TimeLeft(startup_seconds=0.7)
    estimate.record(estimated=10.0, measured=20.0 + OVERHEAD * 2)  # real files are twice as slow
    assert estimate.seconds_left([30.0]) == pytest.approx(2 * (30 + OVERHEAD), rel=0.01)


def test_the_correction_is_bounded() -> None:
    estimate = TimeLeft(startup_seconds=0)
    estimate.record(estimated=0.0001, measured=3.0)  # a tiny file dominated by fixed costs
    assert estimate.seconds_left([100.0]) <= 5 * (100 + OVERHEAD) + 1e-9
    fast = TimeLeft(startup_seconds=0)
    fast.record(estimated=100.0, measured=0.001)
    assert fast.seconds_left([100.0]) >= 0.2 * (100 + OVERHEAD) - 1e-9


def test_nothing_left() -> None:
    estimate = TimeLeft(startup_seconds=0.7)
    estimate.record(estimated=1.0, measured=1.0)
    assert estimate.seconds_left([]) == 0
