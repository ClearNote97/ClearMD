"""How a rejected file is told to the user (UX contract §3), the same in every interface and in
the summary: its kind (skipped before converting, failed or stopped while converting), the
precise reason (with the file's value and the limit when a limit is the reason) and what to do,
or that there is nothing to do."""

from clearmd.backend.schemas.errors import ErrorCode, SkipReason
from clearmd.backend.schemas.models import ConversionOutcome, SkippedItem
from clearmd.i18n import Catalog

# The reasons whose value and limit are sizes in bytes; the others are counts or a ratio.
_SIZES = frozenset(
    {
        SkipReason.TOO_LARGE,
        SkipReason.ARCHIVE_TOO_LARGE,
        SkipReason.TOO_MUCH_MEMORY,
        SkipReason.TOO_MUCH_MEMORY_FOR_ARTICLE,
    }
)


def skip_reason(catalog: Catalog, item: SkippedItem) -> str:
    if item.measured is None or item.limit is None:
        return catalog.text(item.reason.key)
    if item.reason in _SIZES:
        measured, limit = catalog.size(int(item.measured)), catalog.size(int(item.limit))
    else:
        measured, limit = catalog.count(round(item.measured)), catalog.count(round(item.limit))
    return catalog.text(item.reason.key, measured=measured, limit=limit)


def skip_action(catalog: Catalog, item: SkippedItem) -> str:
    return catalog.text(f"skip_action.{item.reason.value}")


def skipped_line(catalog: Catalog, item: SkippedItem, name: str) -> str:
    return catalog.text(
        "cli.skipped",
        name=name,
        reason=skip_reason(catalog, item),
        action=skip_action(catalog, item),
    )


def stopped_message(catalog: Catalog, outcome: ConversionOutcome) -> str:
    """What stopped the file, with the limit it reached."""
    if outcome.error is None:
        raise ValueError("a stopped outcome has an error code")
    if outcome.limit is None:
        return catalog.text(outcome.error.message_key)
    if outcome.error is ErrorCode.TIMED_OUT and outcome.limit % 60:
        limit = catalog.text("time.seconds", seconds=round(outcome.limit))
    elif outcome.error is ErrorCode.TIMED_OUT:
        limit = catalog.text("time.exact_minutes", minutes=round(outcome.limit / 60))
    else:
        limit = catalog.size(int(outcome.limit))
    return catalog.text(f"stop.{outcome.error.value}", limit=limit)


def failed_line(catalog: Catalog, outcome: ConversionOutcome, name: str) -> str:
    if outcome.error is None:
        raise ValueError("a failed outcome has an error code")
    return catalog.text("cli.failed", name=name, message=catalog.error(outcome.error))
