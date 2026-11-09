"""How a rejected file is told to the user (UX contract §3), the same in every interface and in
the summary: its kind (skipped before converting, failed or stopped while converting), the
precise reason (with the file's value and the limit when a limit is the reason) and what to do,
or that there is nothing to do."""

from clearmd.backend.schemas.errors import ErrorCode, SkipReason
from clearmd.backend.schemas.formats import EXTENSIONS, MARKDOWN_EXTENSIONS, FormatId
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
    if item.reason in _SPLIT_SKIPS and not splittable_path(item):
        return catalog.text(f"skip_action.{item.reason.value}_other")
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
    return catalog.text("cli.failed", name=name, message=error_text(catalog, outcome))


# Only these formats can be split (features 023, 024, 027): advice to "split it" names Split for
# them, and the original program for the others (audit 2026-11-09, B4-02).
SPLITTABLE = frozenset({FormatId.PDF, FormatId.MARKDOWN, FormatId.TXT, FormatId.CSV, FormatId.XLSX})
_SPLIT_ADVICE = frozenset({ErrorCode.TIMED_OUT, ErrorCode.OUT_OF_MEMORY, ErrorCode.WORKER_CRASHED})
_SPLIT_SKIPS = frozenset({SkipReason.TOO_LARGE, SkipReason.TOO_MUCH_MEMORY})


def error_action(catalog: Catalog, outcome: ConversionOutcome) -> str:
    """What to do about a failure or a stop: "split it" only for a format Split takes."""
    if outcome.error is None:
        raise ValueError("a failed or stopped outcome has an error code")
    key = outcome.error.action_key
    if outcome.error in _SPLIT_ADVICE and outcome.item.detection.format not in SPLITTABLE:
        key += "_other"
    return catalog.text(key)


def error_text(catalog: Catalog, outcome: ConversionOutcome) -> str:
    """The failure's message and what to do about it."""
    assert outcome.error is not None
    return f"{catalog.text(outcome.error.message_key)} {error_action(catalog, outcome)}"


def splittable_path(item: SkippedItem) -> bool:
    suffix = item.path.suffix.lower()
    return suffix in MARKDOWN_EXTENSIONS or EXTENSIONS.get(suffix) in SPLITTABLE
