"""Each ClearMD_Output folder's summary after a batch: Markdown, Markdown + PDF, or the PDF alone
(ADR-0031, feature 020). A summary that cannot be written never stops the batch: it is told."""

from pathlib import Path

from clearmd.backend.api import composition
from clearmd.backend.schemas.errors import ErrorCode
from clearmd.backend.schemas.formats import PDF_SUMMARY_NAME, SUMMARY_NAME
from clearmd.backend.schemas.models import BatchReport, OutputRootReport
from clearmd.backend.use_cases.output_files import remove_regular_file
from clearmd.backend.use_cases.reporting import by_output_root


def write_summaries(
    report: BatchReport, language: str, *, summary_pdf: bool, summary_markdown: bool
) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    """(the roots whose summary could not be written, those whose PDF could not)."""
    writer = composition.build_summary_writer(language)
    pdf_only = not summary_markdown
    reporter = composition.build_pdf_report(language) if summary_pdf or pdf_only else None
    unwritten: list[Path] = []
    unwritten_pdfs: list[Path] = []
    for root_report in by_output_root(report):
        if pdf_only and reporter is not None:
            try:
                reporter.write(root_report)
            except Exception:  # noqa: BLE001 -- told; the Markdown summary is written instead
                unwritten_pdfs.append(root_report.root)
            else:
                _remove_old(root_report.root, SUMMARY_NAME)  # never a stale Markdown beside it
                continue
        try:
            writer.write(root_report)
        except (OSError, ValueError):  # ValueError: e.g. text that cannot be encoded
            if not _root_was_refused(root_report):  # those already say why, file by file
                unwritten.append(root_report.root)
            _remove_old_pdf(root_report.root)
            continue
        written = False
        if reporter is not None and not pdf_only:
            try:
                reporter.write(root_report)
                written = True
            except Exception:  # noqa: BLE001 -- the Markdown is written: the batch goes on, told
                unwritten_pdfs.append(root_report.root)
        if not written and not pdf_only:
            _remove_old_pdf(root_report.root)
    return tuple(unwritten), tuple(unwritten_pdfs)


def _remove_old_pdf(root: Path) -> None:
    """A PDF summary from an earlier batch never stays next to a newer Markdown one (code review
    of 009)."""
    _remove_old(root, PDF_SUMMARY_NAME)


def _remove_old(root: Path, name: str) -> None:
    """An earlier batch's summary that the new one replaces (a PDF beside a newer Markdown, a
    Markdown beside a newer PDF alone, 020). Only a regular file is removed, never a link."""
    try:
        remove_regular_file(root / name, inside=root)
    except OSError:  # none, or it cannot be removed: nothing more to do
        pass


def _root_was_refused(root_report: OutputRootReport) -> bool:
    refused = {ErrorCode.PERMISSION_DENIED, ErrorCode.WRITE_FAILED}
    return all(outcome.error in refused for outcome in root_report.outcomes)
