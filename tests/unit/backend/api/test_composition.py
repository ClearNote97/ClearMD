from clearmd.backend.api.composition import worker_memory_limit
from clearmd.backend.schemas.limits import GIB


def test_worker_memory_is_half_the_ram_at_most_4_gib() -> None:
    assert worker_memory_limit(total_ram=16 * GIB) == 4 * GIB
    assert worker_memory_limit(total_ram=6 * GIB) == 3 * GIB
