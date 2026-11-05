"""Refactor R01 (ADR-0039): every fixture corpus, in every output mode, converts to exactly the
bytes recorded in ``tests/golden/manifest.txt``. A moved module that changes one byte fails here."""

import sys

import pytest
from support.golden import MANIFEST, outputs


@pytest.mark.skipif(sys.platform == "win32", reason="recorded on Linux: the refactor's gate")
def test_every_fixture_converts_to_the_recorded_bytes() -> None:
    expected = set(MANIFEST.read_text(encoding="utf-8").splitlines())
    actual = set(outputs())
    assert (sorted(expected - actual), sorted(actual - expected)) == ([], [])
