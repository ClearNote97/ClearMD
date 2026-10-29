"""The command-line interface (feature 001): plan, ask if needed, convert, summarize.

Every text comes from the catalogs (ADR-0012). Progress, prompts and notes go to stderr; the final
summary goes to stdout. The batch runs in a thread so that Ctrl+C reaches the main thread at once
and cancels it (AC-26).
"""

import argparse
import multiprocessing
import sys
import threading
from collections.abc import Callable, Sequence
from importlib.metadata import version
from pathlib import Path
from typing import TextIO

from clearmd.backend.api import (
    CancelToken,
    Strategy,
    failed_line,
    load_settings,
    open_folder,
    plan_batch,
    run_batch,
    skipped_line,
    stopped_message,
)
from clearmd.backend.schemas.errors import ErrorCode
from clearmd.backend.schemas.events import BatchEvent, ConversionFinished, ConversionStarted
from clearmd.backend.schemas.models import (
    BatchPlan,
    BatchReport,
    OutcomeStatus,
    PlannedConversion,
)
from clearmd.backend.schemas.settings import SettingsWarning
from clearmd.i18n import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    Catalog,
    load_catalog,
    printable,
    resolve_language,
)

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2
EXIT_DECISION_REQUIRED = 3
EXIT_CANCELLED = 130
PROMPT_ATTEMPTS = 3

Decision = Callable[[PlannedConversion], bool]


def build_parser(catalog: Catalog) -> argparse.ArgumentParser:
    help_ = catalog.text
    parser = argparse.ArgumentParser(prog="clearmd", description=help_("cli.help.description"))
    parser.add_argument("paths", nargs="+", type=Path, metavar="PATH", help=help_("cli.help.paths"))
    existing = parser.add_mutually_exclusive_group()
    existing.add_argument("--overwrite", action="store_true", help=help_("cli.help.overwrite"))
    existing.add_argument("--skip", action="store_true", help=help_("cli.help.skip"))
    parser.add_argument(
        "--recursive",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=help_("cli.help.recursive"),
    )
    parser.add_argument(
        "--output-root", type=Path, metavar="DIR", help=help_("cli.help.output_root")
    )
    parser.add_argument(
        "--html", choices=[strategy.value for strategy in Strategy], help=help_("cli.help.html")
    )
    parser.add_argument(
        "--summary-pdf",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=help_("cli.help.summary_pdf"),
    )
    parser.add_argument("--dry-run", action="store_true", help=help_("cli.help.dry_run"))
    parser.add_argument("--open", action="store_true", help=help_("cli.help.open"))
    parser.add_argument("--lang", choices=SUPPORTED_LANGUAGES, help=help_("cli.help.lang"))
    parser.add_argument("-q", "--quiet", action="store_true", help=help_("cli.help.quiet"))
    parser.add_argument("--version", action="version", version=f"%(prog)s {version('clearmd')}")
    return parser


def _requested_language(argv: Sequence[str] | None) -> str | None:
    """``--lang`` is read first, so that even the help and the settings warnings use it."""
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--lang", choices=SUPPORTED_LANGUAGES)
    known, _ = pre.parse_known_args(argv)
    language: str | None = known.lang
    return language


# --- Terminal I/O (replaceable in the tests) ---------------------------------------------------


def _is_interactive() -> bool:
    return sys.stdin.isatty()


def _ask(prompt: str) -> str | None:
    """One answer from the user, or ``None`` at the end of input."""
    print(prompt, end="", file=sys.stderr, flush=True)
    line = sys.stdin.readline()
    return line.strip() if line else None


# --- Output ----------------------------------------------------------------------------------


class _Progress:
    def __init__(self, catalog: Catalog, *, quiet: bool, stream: TextIO) -> None:
        self._catalog, self._quiet, self._stream = catalog, quiet, stream
        self._hinted = False

    def __call__(self, event: BatchEvent) -> None:
        if isinstance(event, ConversionStarted) and not self._quiet:
            line = self._catalog.text(
                "cli.progress",
                index=event.index,
                total=event.total,
                name=_p(event.item.source.name),
            )
            if event.seconds_left is not None:
                duration = self._catalog.duration(event.seconds_left)
                line = f"{line} · {self._catalog.text('cli.time_left', duration=duration)}"
            print(line, file=self._stream)
        elif isinstance(event, ConversionFinished) and event.outcome.notes and not self._quiet:
            name = _p(event.outcome.item.source.name)
            print(self._catalog.text("cli.converted_with_notes", name=name), file=self._stream)
        elif isinstance(event, ConversionFinished) and event.outcome.error is not None:
            outcome = event.outcome
            assert outcome.error is not None
            name = _p(outcome.item.source.name)
            if outcome.status is OutcomeStatus.STOPPED:
                line = self._catalog.text(
                    "cli.stopped",
                    name=name,
                    message=stopped_message(self._catalog, outcome),
                    elapsed=self._catalog.clock(outcome.seconds),
                    percent=outcome.share_done,
                    action=self._catalog.text(outcome.error.action_key),
                )
            else:
                line = failed_line(self._catalog, outcome, name)
            print(line, file=self._stream)
            if outcome.error is ErrorCode.PERMISSION_DENIED and not self._hinted:
                self._hinted = True
                print(self._catalog.text("cli.hint_output_root"), file=self._stream)


def _print_summary(catalog: Catalog, report: BatchReport) -> None:
    count = {status: 0 for status in OutcomeStatus}
    for outcome in report.outcomes:
        count[outcome.status] += 1
    skipped = len(report.skipped) + count[OutcomeStatus.KEPT]
    line = catalog.text(
        "cli.summary",
        converted=count[OutcomeStatus.CONVERTED],
        skipped=skipped,
        failed=count[OutcomeStatus.FAILED],
    )
    if count[OutcomeStatus.STOPPED]:
        line += catalog.text("cli.summary_stopped", stopped=count[OutcomeStatus.STOPPED])
    print(line)
    for root in _output_roots(report):
        print(catalog.text("cli.results", path=_p(root)))
    for root in report.unwritten_summaries:
        print(catalog.text("cli.summary_not_written", path=_p(root)), file=sys.stderr)
    for root in report.unwritten_pdfs:
        print(catalog.text("cli.pdf_not_written", path=_p(root)), file=sys.stderr)


def _summary_roots(report: BatchReport) -> list[Path]:
    """The output folders worth opening: those whose summary was written (it says what happened,
    even when every file failed). A folder refused as a link has none."""
    unwritten = set(report.unwritten_summaries)
    return [root for root in _output_roots(report) if root not in unwritten]


def _output_roots(report: BatchReport) -> list[Path]:
    return list(dict.fromkeys(outcome.item.output_root for outcome in report.outcomes))


def _p(value: object) -> str:
    """A name or path as it may be printed: control characters escaped (security review)."""
    return printable(str(value))


def _shown(path: Path, is_dir: bool) -> str:
    return _p(f"{path.name}/" if is_dir else path.name)


def _print_plan_notes(catalog: Catalog, plan: BatchPlan, *, quiet: bool, stream: TextIO) -> None:
    for problem in plan.input_errors:
        print(catalog.text("cli.input_not_found", path=_p(problem.path)), file=stream)
    if not quiet:
        for item in plan.skipped:
            print(skipped_line(catalog, item, _shown(item.path, item.is_dir)), file=stream)
    for warning in plan.warnings:
        line = catalog.text(
            "cli.warning_slow",
            name=_p(warning.item.source.name),
            limit=catalog.text("time.exact_minutes", minutes=round(warning.limit_seconds / 60)),
            estimate=catalog.duration(warning.estimated_seconds),
        )
        print(line, file=stream)


def _print_settings_warnings(
    catalog: Catalog, warnings: Sequence[SettingsWarning], stream: TextIO
) -> None:
    for warning in warnings:
        print(catalog.text(f"settings.{warning.problem.value}", setting=warning.key), file=stream)


def _print_dry_run(catalog: Catalog, plan: BatchPlan) -> None:
    for item in plan.conversions:
        target = item.target.relative_to(item.output_root.parent)
        line = catalog.text("cli.dry_run_item", source=_p(item.source), target=_p(target))
        if item.exists:
            line += catalog.text("cli.dry_run_exists")
        print(line)
    print(catalog.text("cli.dry_run_done", count=len(plan.conversions)))


# --- Decisions about existing outputs (AC-14 - AC-16) -----------------------------------------


def _ask_once(catalog: Catalog, plan: BatchPlan) -> Decision:
    """One question for the whole batch; any doubt means the safe answer: keep them."""
    prompt = catalog.text("cli.ask_existing", count=len(plan.existing))
    for _ in range(PROMPT_ATTEMPTS):
        answer = _ask(prompt)
        if answer is None:
            break
        if answer == "1":
            return lambda item: True
        if answer == "2":
            return lambda item: False
        if answer == "3":
            yes = catalog.text("cli.yes_letter").casefold()
            chosen = set()
            for item in plan.existing:
                target = item.target.relative_to(item.output_root.parent)
                reply = _ask(catalog.text("cli.ask_one", target=_p(target)))
                if reply is not None and reply.casefold().startswith(yes):
                    chosen.add(item.target)
            return lambda item: item.target in chosen
    return lambda item: False


def _decision(
    catalog: Catalog, plan: BatchPlan, on_existing: str, stream: TextIO
) -> Decision | None:
    """``None`` when a decision is required but nobody can answer (exit 3, AC-18)."""
    if on_existing == "overwrite":
        return lambda item: True
    if on_existing == "skip" or not plan.existing:
        return lambda item: False
    if not _is_interactive():
        print(catalog.text("cli.decision_required", count=len(plan.existing)), file=stream)
        return None
    return _ask_once(catalog, plan)


# --- The batch -------------------------------------------------------------------------------


def _run_cancellable(
    catalog: Catalog,
    plan: BatchPlan,
    decision: Decision,
    progress: _Progress,
    stream: TextIO,
    *,
    summary_pdf: bool = False,
) -> BatchReport:
    """Run the batch in a thread; Ctrl+C cancels it at once and its summary is still written."""
    cancel = CancelToken()
    reports: list[BatchReport] = []
    errors: list[BaseException] = []
    # An event, not Thread.join: on Python 3.12 a join interrupted by Ctrl+C marks the thread as
    # finished, and the next join returns before the batch has ended (CI of feature 006).
    done = threading.Event()

    def work() -> None:
        try:
            report = run_batch(
                plan,
                overwrite=decision,
                on_event=progress,
                cancel=cancel,
                language=catalog.language,
                summary_pdf=summary_pdf,
            )
        except BaseException as error:  # re-raised in the main thread
            errors.append(error)
        else:
            reports.append(report)
        finally:
            done.set()

    threading.Thread(target=work, name="clearmd-batch", daemon=True).start()
    try:
        while not done.wait(0.2):
            pass
    except KeyboardInterrupt:
        cancel.cancel()
        print(catalog.text("cli.cancelling"), file=stream)
        done.wait()  # a second Ctrl+C here stops the process for good
    if errors:
        raise errors[0]
    return reports[0]


def _exit_code(report: BatchReport) -> int:
    if report.cancelled:
        return EXIT_CANCELLED
    unfinished = {OutcomeStatus.FAILED, OutcomeStatus.STOPPED}
    if any(outcome.status in unfinished for outcome in report.outcomes):
        return EXIT_FAILED
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    multiprocessing.freeze_support()  # a no-op unless running as a packaged executable
    try:
        return _main(argv)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as error:  # the last net: a message, never a traceback (UX contract)
        catalog = load_catalog(resolve_language(_requested_language(argv), DEFAULT_LANGUAGE))
        detail = _p(f"{type(error).__name__}: {error}")
        print(catalog.text("cli.unexpected_error", detail=detail), file=sys.stderr)
        return EXIT_FAILED


def _main(argv: Sequence[str] | None) -> int:
    settings, settings_warnings = load_settings()
    catalog = load_catalog(resolve_language(_requested_language(argv), settings.language))
    args = build_parser(catalog).parse_args(argv)
    err = sys.stderr
    _print_settings_warnings(catalog, settings_warnings, err)

    # A flag decides for this run only; without one, the shared settings do (AC-34).
    recursive = settings.recursive if args.recursive is None else args.recursive
    on_existing = (
        "overwrite" if args.overwrite else "skip" if args.skip else settings.on_existing_output
    )
    try:
        plan = plan_batch(
            args.paths,
            recursive=recursive,
            output_root=args.output_root,
            html_strategy=Strategy(args.html or settings.html_strategy),
        )
    except KeyboardInterrupt:
        print(catalog.text("cli.cancelled_before_start"), file=err)
        return EXIT_CANCELLED
    _print_plan_notes(catalog, plan, quiet=args.quiet, stream=err)
    if plan.is_empty:
        if plan.input_errors and not plan.skipped:
            print(catalog.text("cli.no_valid_input"), file=err)
            return EXIT_USAGE
        print(catalog.text("cli.nothing_to_convert"))
        return EXIT_OK
    if args.dry_run:
        _print_dry_run(catalog, plan)
        return EXIT_OK

    try:
        decision = _decision(catalog, plan, on_existing, err)
    except KeyboardInterrupt:
        print(catalog.text("cli.cancelled_before_start"), file=err)
        return EXIT_CANCELLED
    if decision is None:
        return EXIT_DECISION_REQUIRED
    progress = _Progress(catalog, quiet=args.quiet, stream=err)
    # A flag decides for this run only (--summary-pdf, --no-summary-pdf); without one, the setting.
    summary_pdf = (
        settings.summary_format == "markdown_pdf" if args.summary_pdf is None else args.summary_pdf
    )
    report = _run_cancellable(catalog, plan, decision, progress, err, summary_pdf=summary_pdf)
    _print_summary(catalog, report)
    if args.open:
        for root in _summary_roots(report):
            try:
                open_folder(root)
            except (OSError, ValueError):  # a root refused as a link, no file browser…
                print(catalog.text("cli.cannot_open", path=_p(root)), file=err)
    return _exit_code(report)
