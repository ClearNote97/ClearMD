"""The progress printer: one line per event on stderr."""

from typing import TextIO

from clearmd.backend.api import failed_line, stopped_message
from clearmd.backend.schemas.errors import ErrorCode
from clearmd.backend.schemas.events import BatchEvent, ConversionFinished, ConversionStarted
from clearmd.backend.schemas.models import OutcomeStatus
from clearmd.frontend.cli.report import p
from clearmd.i18n import Catalog


class Progress:
    def __init__(self, catalog: Catalog, *, quiet: bool, stream: TextIO) -> None:
        self._catalog, self._quiet, self._stream = catalog, quiet, stream
        self._hinted = False

    def __call__(self, event: BatchEvent) -> None:
        if isinstance(event, ConversionStarted) and not self._quiet:
            line = self._catalog.text(
                "cli.progress",
                index=event.index,
                total=event.total,
                name=p(event.item.source.name),
            )
            if event.seconds_left is not None:
                duration = self._catalog.duration(event.seconds_left)
                line = f"{line} · {self._catalog.text('cli.time_left', duration=duration)}"
            print(line, file=self._stream)
        elif (
            isinstance(event, ConversionFinished) and event.outcome.worth_a_look and not self._quiet
        ):
            name = p(event.outcome.item.source.name)
            print(self._catalog.text("cli.converted_with_notes", name=name), file=self._stream)
        elif isinstance(event, ConversionFinished) and event.outcome.error is not None:
            outcome = event.outcome
            assert outcome.error is not None
            name = p(outcome.item.source.name)
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
