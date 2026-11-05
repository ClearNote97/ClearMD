"""Executing a plan: outcomes, cancelling and notes."""

from pathlib import Path

from support.execution_fakes import NOW, FakeRunner, _item, _plan, _run

from clearmd.backend.schemas.errors import ErrorCode
from clearmd.backend.schemas.events import ConversionFinished, ConversionStarted
from clearmd.backend.schemas.models import (
    OutcomeStatus,
    PlannedConversion,
)
from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind


def test_converted_files_are_written_utf8_with_lf(tmp_path: Path) -> None:
    item = _item(tmp_path, "report.pdf")
    events, report = _run(_plan(item), FakeRunner())
    assert item.target.read_bytes() == b"# report\nline two\n"
    assert [o.status for o in report.outcomes] == [OutcomeStatus.CONVERTED]
    assert [type(e) for e in events] == [ConversionStarted, ConversionFinished]


def test_a_failure_does_not_stop_the_batch(tmp_path: Path) -> None:
    items = (_item(tmp_path, "corrupt.pdf"), _item(tmp_path, "good.pdf"))
    _, report = _run(_plan(*items), FakeRunner())
    outcomes = report.outcomes
    assert [o.status for o in outcomes] == [OutcomeStatus.FAILED, OutcomeStatus.CONVERTED]
    assert outcomes[0].error is ErrorCode.CORRUPT_FILE
    assert outcomes[0].detail == "BadZipFile: File is not a zip file"
    assert not items[0].target.exists()
    assert items[1].target.exists()


def test_existing_outputs_are_kept_when_the_caller_says_so(tmp_path: Path) -> None:
    item = _item(tmp_path, "report.pdf", exists=True)
    item.target.parent.mkdir(parents=True)
    item.target.write_text("old", encoding="utf-8")
    runner = FakeRunner()
    _, report = _run(_plan(item), runner, overwrite=lambda item: False)
    assert item.target.read_text(encoding="utf-8") == "old"
    assert runner.seen == []
    assert [o.status for o in report.outcomes] == [OutcomeStatus.KEPT]


def test_cancelling_marks_the_current_and_the_rest_as_cancelled(tmp_path: Path) -> None:
    items = (
        _item(tmp_path, "first.pdf"),
        _item(tmp_path, "cancel.pdf"),
        _item(tmp_path, "last.pdf"),
    )
    runner = FakeRunner()
    _, report = _run(_plan(*items), runner)
    statuses = [o.status for o in report.outcomes]
    assert statuses == [OutcomeStatus.CONVERTED, OutcomeStatus.CANCELLED, OutcomeStatus.CANCELLED]
    assert report.cancelled
    assert runner.seen == ["first.pdf", "cancel.pdf"]
    assert not items[1].target.exists()


def test_report_carries_the_clock_and_the_plan(tmp_path: Path) -> None:
    _, report = _run(_plan(_item(tmp_path, "a.pdf")), FakeRunner())
    assert report.started_at == NOW
    assert report.finished_at == NOW


def test_an_output_that_appeared_after_planning_is_not_overwritten_silently(tmp_path: Path) -> None:
    item = _item(tmp_path, "report.pdf")  # planned as not existing
    item.target.parent.mkdir(parents=True)
    item.target.write_text("written meanwhile", encoding="utf-8")
    asked: list[Path] = []

    def overwrite(planned: PlannedConversion) -> bool:
        asked.append(planned.target)
        return False

    _, report = _run(_plan(item), FakeRunner(), overwrite=overwrite)
    assert asked == [item.target]
    assert item.target.read_text(encoding="utf-8") == "written meanwhile"
    assert [o.status for o in report.outcomes] == [OutcomeStatus.KEPT]


def test_notes_are_kept_in_the_outcome_and_the_file_is_still_converted(tmp_path: Path) -> None:
    _, report = _run(
        _plan(_item(tmp_path, "noted.pdf"), _item(tmp_path, "plain.pdf")), FakeRunner()
    )
    noted, plain = report.outcomes
    assert noted.status is OutcomeStatus.CONVERTED
    assert noted.notes == (ConversionNote(NoteKind.UNKNOWN_COMMANDS, (NoteItem("\\x"),)),)
    assert plain.notes == ()
