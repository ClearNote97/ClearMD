"""The queue order: cheapest first, ties by path (ADR-0015, AC-20)."""

from collections.abc import Iterable

from clearmd.backend.schemas.models import PlannedConversion


def order_by_cost(conversions: Iterable[PlannedConversion]) -> tuple[PlannedConversion, ...]:
    """Shortest job first: results appear soon, a cancellation keeps the most finished files."""
    return tuple(
        sorted(
            conversions,
            key=lambda item: (item.cost, str(item.source).casefold(), str(item.source)),
        )
    )
