"""GUI tests run on a display: the session's, or a virtual one started for the run."""

from collections.abc import Iterator

import pytest
from support.display import virtual_display


@pytest.fixture(scope="session")
def display() -> Iterator[str]:
    with virtual_display() as name:
        if name is None:
            pytest.skip("no display and no Xvfb: GUI tests need one")
        yield name
