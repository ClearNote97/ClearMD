"""The batch: run it so that Ctrl+C reaches the main thread, and the exit codes."""

import threading
from typing import TextIO

from clearmd.backend.api import CancelToken, run_batch
from clearmd.backend.schemas.models import BatchPlan, BatchReport, OutcomeStatus
from clearmd.frontend.cli.progress import Progress
from clearmd.frontend.cli.prompts import Decision
from clearmd.i18n import Catalog

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2
EXIT_DECISION_REQUIRED = 3
EXIT_CANCELLED = 130


def run_cancellable(
    catalog: Catalog,
    plan: BatchPlan,
    decision: Decision,
    progress: Progress,
    stream: TextIO,
    *,
    summary_pdf: bool = False,
    summary_markdown: bool = True,
    images: bool = False,
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
                summary_markdown=summary_markdown,
                images=images,
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


def exit_code(report: BatchReport) -> int:
    if report.cancelled:
        return EXIT_CANCELLED
    unfinished = {OutcomeStatus.FAILED, OutcomeStatus.STOPPED}
    if any(outcome.status in unfinished for outcome in report.outcomes):
        return EXIT_FAILED
    return EXIT_OK
