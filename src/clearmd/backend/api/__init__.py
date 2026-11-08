"""The facade every interface calls (ADR-0014): plan a batch, then run it."""

import os
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from clearmd.backend.api import composition
from clearmd.backend.api.naming import STAMP, named
from clearmd.backend.api.summaries import write_summaries
from clearmd.backend.schemas.events import BatchEvent
from clearmd.backend.schemas.formats import Strategy
from clearmd.backend.schemas.merge import Into
from clearmd.backend.schemas.models import (
    BatchPlan,
    BatchReport,
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
from clearmd.backend.use_cases.changes import changed_since_result
from clearmd.backend.use_cases.execution import execute_plan
from clearmd.backend.use_cases.merging import execute_merge
from clearmd.backend.use_cases.planning import build_plan
from clearmd.backend.use_cases.split_advice import large_in_plan, large_in_report, most_parts
from clearmd.i18n import load_catalog

__all__ = [
    "CancelToken",
    "Into",
    "Cut",
    "Keep",
    "SplitSpec",
    "Strategy",
    "changed_since_result",
    "failed_line",
    "large_in_plan",
    "large_in_report",
    "most_parts",
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
    merge: Into | None = None,
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
            merge=merge,
            stamp=datetime.now().strftime(STAMP),
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
    plan = named(plan, language)
    runner = composition.build_runner(composition.default_limits())
    pages = composition.build_page_runner(runner)
    try:
        if plan.merge is not None:  # Merge (feature 026): every document into one file
            report = execute_merge(
                plan,
                runner=runner,
                cutter=pages,
                on_event=on_event or _ignore,
                cancel=cancel or CancelToken(),
                clock=composition.build_clock(),
            )
        else:
            report = execute_plan(
                plan,
                overwrite=overwrite,
                runner=runner,
                on_event=on_event or _ignore,
                cancel=cancel or CancelToken(),
                clock=composition.build_clock(),
                startup_seconds=composition.default_limits().worker_startup_seconds,
                cutter=pages,
            )
    finally:
        runner.close()
    unwritten, unwritten_pdfs = write_summaries(
        report, language, summary_pdf=summary_pdf, summary_markdown=summary_markdown
    )
    return replace(report, unwritten_summaries=unwritten, unwritten_pdfs=unwritten_pdfs)
