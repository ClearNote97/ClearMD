"""The facade every interface calls (ADR-0014): plan a batch, then run it."""

import os
from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path

from clearmd.backend.api import composition
from clearmd.backend.schemas.errors import ErrorCode
from clearmd.backend.schemas.events import BatchEvent
from clearmd.backend.schemas.formats import PDF_SUMMARY_NAME, SUMMARY_NAME, Strategy
from clearmd.backend.schemas.models import (
    BatchPlan,
    BatchReport,
    OutputRootReport,
    PlannedConversion,
)
from clearmd.backend.schemas.settings import Settings, SettingsWarning
from clearmd.backend.schemas.split import Cut, Keep, SplitSpec
from clearmd.backend.services import folders, settings_store
from clearmd.backend.services.rejections import (
    failed_line,
    skip_action,
    skip_reason,
    skipped_line,
    stopped_message,
)
from clearmd.backend.use_cases.cancel import CancelToken
from clearmd.backend.use_cases.execution import execute_plan
from clearmd.backend.use_cases.output_files import remove_regular_file
from clearmd.backend.use_cases.planning import build_plan
from clearmd.backend.use_cases.reporting import by_output_root
from clearmd.i18n import load_catalog

__all__ = [
    "CancelToken",
    "Cut",
    "Keep",
    "SplitSpec",
    "Strategy",
    "failed_line",
    "load_settings",
    "open_folder",
    "plan_batch",
    "run_batch",
    "save_settings",
    "settings_path",
    "skip_action",
    "skip_reason",
    "skipped_line",
    "stopped_message",
]


def load_settings() -> tuple[Settings, tuple[SettingsWarning, ...]]:
    """The shared settings.toml; defaults (and warnings) when missing or invalid (AC-33)."""
    return settings_store.load_settings()


def settings_path() -> Path:
    return settings_store.settings_path()


def save_settings(settings: Settings) -> None:
    """Write the shared settings.toml atomically (the GUIs, ADR-0026); ``OSError`` if it cannot."""
    settings_store.save_settings(settings)


def open_folder(path: Path) -> None:
    """Show a results folder in the system file browser (only a real folder; ``ValueError``)."""
    folders.open_folder(path)


def _ignore(event: BatchEvent) -> None:
    pass


def plan_batch(
    inputs: Sequence[Path],
    *,
    recursive: bool = True,
    output_root: Path | None = None,
    on_event: Callable[[BatchEvent], None] | None = None,
    html_strategy: Strategy = Strategy.FULL,
    cancel: CancelToken | None = None,
    split: SplitSpec | None = None,
) -> BatchPlan:
    """Everything that would happen, computed without writing anything.

    The worker starts only if a file needs detection by content. A cancelled ``cancel`` stops
    the scan and the detection early: the plan is then incomplete, for the caller to drop.
    """
    limits = composition.default_limits()
    worker = composition.build_runner(limits)
    try:
        return build_plan(
            # Absolute, without resolving symlinks: a link given as input must stay a link.
            [Path(os.path.abspath(path.expanduser())) for path in inputs],
            detector=composition.build_detector(worker),
            limits=limits,
            recursive=recursive,
            output_root=Path(os.path.abspath(output_root.expanduser())) if output_root else None,
            on_event=on_event,
            html_strategy=html_strategy,
            cancel=cancel,
            split=split,
        )
    finally:
        worker.close()


def run_batch(
    plan: BatchPlan,
    *,
    overwrite: Callable[[PlannedConversion], bool],
    on_event: Callable[[BatchEvent], None] | None = None,
    cancel: CancelToken | None = None,
    language: str = "en",
    summary_pdf: bool = False,
    summary_markdown: bool = True,
    images: bool = False,
) -> BatchReport:
    """Convert every planned file in the worker process, write the results and, in each
    ClearMD_Output folder, its Resumen_ClearMD.md (also when the batch was cancelled), and its
    Resumen_ClearMD.pdf when ``summary_pdf`` (ADR-0031). ``summary_markdown=False`` (with
    ``summary_pdf``): the PDF alone (feature 020); if it cannot be written, the Markdown is."""
    if images:  # each document's images in "<name>_images" next to it, in the user's language
        suffix = load_catalog(language).text("images.suffix")
        plan = replace(
            plan,
            conversions=tuple(
                replace(item, images=f"{item.target.stem}{suffix}") for item in plan.conversions
            ),
        )
    plan = _parts_named(plan, language)
    runner = composition.build_runner(composition.default_limits())
    try:
        report = execute_plan(
            plan,
            overwrite=overwrite,
            runner=runner,
            on_event=on_event or _ignore,
            cancel=cancel or CancelToken(),
            clock=composition.build_clock(),
            startup_seconds=composition.default_limits().worker_startup_seconds,
            cutter=runner,
        )
    finally:
        runner.close()
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
    return replace(
        report, unwritten_summaries=tuple(unwritten), unwritten_pdfs=tuple(unwritten_pdfs)
    )


def _parts_named(plan: BatchPlan, language: str) -> BatchPlan:
    """A split file's parts named in the user's language (feature 023)."""
    template = load_catalog(language).text_template("split.part_name")
    return replace(
        plan,
        conversions=tuple(
            replace(item, split=replace(item.split, part_name=template))
            if item.split is not None
            else item
            for item in plan.conversions
        ),
    )


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
