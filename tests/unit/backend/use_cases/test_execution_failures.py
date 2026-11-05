"""Executing a plan: disk and source errors fail only their file."""

import errno
from pathlib import Path

import pytest
from support import WINDOWS
from support.execution_fakes import FakeRunner, _item, _plan, _run

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.models import (
    ConversionResult,
    OutcomeStatus,
    PlannedConversion,
)
from clearmd.backend.use_cases.cancel import CancelToken


def test_a_permission_error_on_one_result_fails_only_that_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import clearmd.backend.use_cases.execution as execution
    from clearmd.backend.use_cases.output_files import atomic_write as real_write

    def deny_first(target: Path, text: str, *, inside: Path) -> None:
        if target.stem == "a":
            raise PermissionError(13, "Permission denied", str(target))  # e.g. locked by an editor
        real_write(target, text, inside=inside)

    monkeypatch.setattr(execution, "atomic_write", deny_first)
    items = (_item(tmp_path, "a.pdf"), _item(tmp_path, "b.pdf"))
    _, report = _run(_plan(*items), FakeRunner())
    assert [(o.status, o.error) for o in report.outcomes] == [
        (OutcomeStatus.FAILED, ErrorCode.WRITE_FAILED),
        (OutcomeStatus.CONVERTED, None),
    ]


def test_an_unreadable_source_fails_only_that_file(tmp_path: Path) -> None:
    class LockedFirst(FakeRunner):
        def convert(self, item: PlannedConversion, cancel: CancelToken) -> ConversionResult:
            if item.source.stem == "locked":
                self.seen.append(item.source.name)
                raise ConversionError(ErrorCode.SOURCE_UNREADABLE, "PermissionError: locked")
            return super().convert(item, cancel)

    items = (_item(tmp_path, "locked.xlsx"), _item(tmp_path, "b.pdf"), _item(tmp_path, "c.pdf"))
    runner = LockedFirst()
    _, report = _run(_plan(*items), runner)
    assert [o.status for o in report.outcomes] == [
        OutcomeStatus.FAILED,
        OutcomeStatus.CONVERTED,
        OutcomeStatus.CONVERTED,
    ]
    assert runner.seen == ["locked.xlsx", "b.pdf", "c.pdf"]


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (OSError(errno.EROFS, "Read-only file system"), ErrorCode.PERMISSION_DENIED),
        (OSError(errno.ENOSPC, "No space left on device"), ErrorCode.WRITE_FAILED),
    ],
)
def test_an_output_root_that_cannot_be_created_fails_its_files_without_crashing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: OSError, code: ErrorCode
) -> None:
    import clearmd.backend.use_cases.execution as execution

    def broken(root: Path) -> None:
        raise error

    monkeypatch.setattr(execution, "prepare_root", broken)
    runner = FakeRunner()
    _, report = _run(_plan(_item(tmp_path, "a.pdf"), _item(tmp_path, "b.pdf")), runner)
    assert [o.error for o in report.outcomes] == [code, code]
    assert runner.seen == []


def test_any_os_error_while_saving_fails_that_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import clearmd.backend.use_cases.execution as execution

    def is_a_directory(target: Path, text: str, *, inside: Path) -> None:
        raise IsADirectoryError(errno.EISDIR, "Is a directory", str(target))

    monkeypatch.setattr(execution, "atomic_write", is_a_directory)
    _, report = _run(_plan(_item(tmp_path, "a.pdf")), FakeRunner())
    (outcome,) = report.outcomes
    assert (outcome.status, outcome.error) == (OutcomeStatus.FAILED, ErrorCode.WRITE_FAILED)


@pytest.mark.skipif(WINDOWS, reason="chmod cannot make a folder unwritable on Windows")
def test_an_unwritable_output_root_fails_its_files_without_converting_them(tmp_path: Path) -> None:
    locked = tmp_path / "locked"
    locked.mkdir()
    free = tmp_path / "free"
    free.mkdir()
    items = (_item(locked, "a.pdf"), _item(locked, "b.pdf"), _item(free, "c.pdf"))
    runner = FakeRunner()
    locked.chmod(0o555)
    try:
        _, report = _run(_plan(*items), runner)
    finally:
        locked.chmod(0o755)
    outcomes = report.outcomes
    assert [o.error for o in outcomes[:2]] == [ErrorCode.PERMISSION_DENIED] * 2
    assert outcomes[2].status is OutcomeStatus.CONVERTED
    assert runner.seen == ["c.pdf"]  # nothing was converted for the locked root
