"""Every rejection says its kind, the precise reason (limit and value) and what to do (UX §3)."""

from pathlib import Path

import pytest

from clearmd.backend.schemas.errors import ErrorCode, SkipReason
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.limits import GIB, MIB
from clearmd.backend.schemas.models import (
    ConversionOutcome,
    Detection,
    DetectionMethod,
    OutcomeStatus,
    PlannedConversion,
    SkippedItem,
)
from clearmd.backend.services.rejections import (
    failed_line,
    skip_action,
    skip_reason,
    skipped_line,
    stopped_message,
)
from clearmd.i18n import SUPPORTED_LANGUAGES, load_catalog

EN = load_catalog("en")
ES = load_catalog("es")


@pytest.mark.parametrize("language", SUPPORTED_LANGUAGES)
@pytest.mark.parametrize("reason", list(SkipReason))
def test_every_skip_reason_has_an_action_in_every_language(
    reason: SkipReason, language: str
) -> None:
    catalog = load_catalog(language)
    item = SkippedItem(Path("x"), reason, measured=2, limit=1)
    assert skip_reason(catalog, item) and skip_action(catalog, item)


@pytest.mark.parametrize(
    ("item", "expected"),
    [
        (SkippedItem(Path("a.pdf"), SkipReason.TOO_LARGE, measured=300 * MIB, limit=250 * MIB),
         "too large (300 MB; the limit is 250 MB)"),
        (SkippedItem(Path("a.docx"), SkipReason.ARCHIVE_TOO_LARGE, measured=3 * GIB, limit=GIB),
         "it would decompress to 3.0 GB; the limit is 1.0 GB"),
        (SkippedItem(Path("a.docx"), SkipReason.ARCHIVE_RATIO, measured=4210.4, limit=100),
         "it would grow 4,210 times when decompressed; the limit is 100"),
        (SkippedItem(Path("a.docx"), SkipReason.ARCHIVE_ENTRIES, measured=80_000, limit=50_000),
         "it holds 80,000 files inside; the limit is 50,000"),
        (SkippedItem(Path("d"), SkipReason.TOO_DEEP, is_dir=True, measured=140, limit=100),
         "folders nested too deeply (140 levels; the limit is 100)"),
    ],
)  # fmt: skip
def test_a_limit_says_the_files_value_and_the_limit(item: SkippedItem, expected: str) -> None:
    assert skip_reason(EN, item) == expected


def test_the_line_says_the_kind_the_reason_and_what_to_do() -> None:
    item = SkippedItem(Path("a.pdf"), SkipReason.TOO_LARGE, measured=300 * MIB, limit=250 * MIB)
    assert skipped_line(EN, item, "a.pdf") == (
        "– Skipped: a.pdf — too large (300 MB; the limit is 250 MB). "
        "Split it into smaller files and try again."
    )
    assert skipped_line(ES, item, "a.pdf").startswith(
        "– Omitido: a.pdf — demasiado grande (300 MB;"
    )


def test_nothing_to_do_is_said_too() -> None:
    item = SkippedItem(Path("ClearMD_Output"), SkipReason.OUTPUT_FOLDER, is_dir=True)
    assert "nothing to do" in skip_action(EN, item).lower()


def test_a_stop_says_the_limit_it_reached() -> None:
    item = _planned()
    timed = ConversionOutcome(item, OutcomeStatus.STOPPED, ErrorCode.TIMED_OUT, limit=600)
    memory = ConversionOutcome(item, OutcomeStatus.STOPPED, ErrorCode.OUT_OF_MEMORY, limit=4 * GIB)
    assert "the limit of 10 min" in stopped_message(EN, timed)
    assert "the limit of 4.0 GB" in stopped_message(EN, memory)
    assert "10 min" in stopped_message(ES, timed)


def test_a_failure_says_its_kind() -> None:
    outcome = ConversionOutcome(_planned(), OutcomeStatus.FAILED, ErrorCode.PASSWORD_PROTECTED)
    assert failed_line(EN, outcome, "a.pdf") == (
        "✗ Failed: a.pdf — This file is password-protected. Remove the password and try again."
    )


def _planned() -> PlannedConversion:
    return PlannedConversion(
        source=Path("a.pdf"),
        output_root=Path("out"),
        target=Path("out/a.md"),
        detection=Detection(FormatId.PDF, DetectionMethod.EXTENSION),
        exists=False,
        cost=10.0,
    )
