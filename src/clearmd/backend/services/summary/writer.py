"""Write Resumen_ClearMD.md for one output folder, in human language (ADR-0016, ADR-0031).

What it says comes from ``content.SummaryContent``; this module only writes it as Markdown. Names
from the user's files are code spans a hostile name cannot close (ADR-0023).
"""

import html
import re
from collections.abc import Iterable
from pathlib import Path

from clearmd.backend.schemas.formats import SUMMARY_NAME
from clearmd.backend.schemas.models import OutputRootReport
from clearmd.backend.schemas.notes import ConversionNote
from clearmd.backend.services.summary.content import SummaryBuilder
from clearmd.backend.services.summary.model import Entry, Mark, SummaryContent
from clearmd.backend.use_cases.output_files import UnsafeOutput, atomic_write, read_regular_file
from clearmd.i18n import Catalog, printable

HISTORY_START = "<!-- clearmd:history -->"
HISTORY_END = "<!-- /clearmd:history -->"
HISTORY_LIMIT = 200
NOTE_ITEMS = 20
# Only lines ClearMD itself wrote survive into the history: date · ClearMD version · totals.
# The counts may have a thousands mark (1,500 / 1.500): a big batch stays in the history too.
_HISTORY_LINE = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} · ClearMD [0-9A-Za-z.+-]+ · [\w ·.,]+")


def _code(text: str) -> str:
    """A one-line code span that an untrusted file name cannot close or break."""
    shown = printable(text)
    longest = max((len(run) for run in re.findall("`+", shown)), default=0)
    fence = "`" * (longest + 1)
    return f"{fence} {shown} {fence}" if longest else f"`{shown}`"


def _cell(text: str) -> str:
    return _code(text).replace("|", "\\|")


def _previous_history(summary: Path) -> tuple[list[str], bool]:
    """Earlier batches, newest first, and whether a previous summary could not be read."""
    try:
        text = read_regular_file(summary)  # a planted link is never read through
    except (UnsafeOutput, OSError, UnicodeDecodeError):
        return [], True
    if text is None:
        return [], False
    lines = text.split("\n")  # never splitlines(): it also breaks on U+2028 and friends
    if HISTORY_START not in lines or HISTORY_END not in lines:
        return [], True
    start = lines.index(HISTORY_START)
    inside = lines[start + 1 : lines.index(HISTORY_END)]
    # The batch line of the last summary: the first of ClearMD's own lines above the history.
    header = next((line for line in lines[:start] if _HISTORY_LINE.fullmatch(line)), "")
    candidates = [header, *(line.removeprefix("- ") for line in inside if line.startswith("- "))]
    return [f"- {line}" for line in candidates if _HISTORY_LINE.fullmatch(line)], False


MARKS = {
    Mark.DONE: "✅",
    Mark.ATTENTION: "⚠️",
    Mark.FAILED: "❌",
    Mark.STOPPED: "⏹️",
}


class MarkdownSummaryWriter:
    """A ``SummaryWriter``: one Markdown file per ClearMD_Output folder, in the user's language."""

    def __init__(self, catalog: Catalog, *, version: str) -> None:
        self._catalog = catalog
        self._builder = SummaryBuilder(catalog, version=version)

    def write(self, report: OutputRootReport) -> None:
        path = report.root / SUMMARY_NAME
        history, unreadable = _previous_history(path)
        rendered = self.render(report, history[:HISTORY_LIMIT], unreadable)
        atomic_write(path, rendered, inside=report.root)

    def render(self, report: OutputRootReport, history: list[str], unreadable: bool) -> str:
        return self.render_content(self._builder.build(report), history, unreadable)

    def render_content(self, content: SummaryContent, history: list[str], unreadable: bool) -> str:
        text = self._catalog.text
        headline = f"{MARKS[content.mark]} **{content.headline}**"
        if content.attention_line:
            headline += f" {content.attention_line}"
        lines = [f"# {text('summary.title')}", "", headline, "", content.batch_line, ""]
        lines += [
            f"## {text('summary.where_title')}",
            text(content.where_key, folder=_code(content.folder + "/")),
            "",
        ]
        lines += self._section("summary.attention", self._attention(content.attention))
        if content.converted:
            lines += [
                f"## {text(content.done_key)}",
                f"| {text('summary.col_document')} | {text('summary.col_folder')} "
                f"| {text('summary.col_result')} | {text('summary.col_format')} "
                f"| {text('summary.col_time')} |",
                "|---|---|---|---|---|",
                *(
                    f"| {_cell(row.name)} | {_cell(row.folder) if row.folder else '—'} "
                    f"| {_cell(row.result)} | {row.format} | {row.time} |"
                    for row in content.converted
                ),
                "",
            ]
        lines += self._section("summary.left_out", (self._line(e) for e in content.left_out))
        kept = (f"{self._line(e)} → {_code(e.result)}" for e in content.kept)
        lines += self._section("summary.kept", kept)
        lines += self._section("summary.cancelled", (self._line(e) for e in content.cancelled))
        # The history, folded: its markers and lines as before (ADR-0016), inside <details>.
        lines += ["<details>", f"<summary>{text('summary.history')}</summary>", ""]
        lines += [HISTORY_START]
        if unreadable:
            lines.append(f"_{text('summary.history_restarted')}_")
        elif not history:
            lines.append(f"_{text('summary.history_empty')}_")
        lines += [*history, HISTORY_END, "", "</details>"]
        return "\n".join(lines) + "\n"

    def _line(self, entry: Entry) -> str:
        mark = f"{MARKS[entry.mark]} " if entry.mark else ""
        place = (
            " " + self._catalog.text("summary.in_folder", folder=_code(entry.folder))
            if entry.folder
            else ""
        )
        message = f" — {entry.message}" if entry.message else ""
        return f"- {mark}{_code(entry.name)}{place}{message}"

    def _attention(self, entries: Iterable[Entry]) -> Iterable[str]:
        summary = self._catalog.text("summary.technical_detail")
        for entry in entries:
            yield self._line(entry)
            for note in entry.notes:
                yield f"  - {self.describe(note)}"
            if entry.detail:
                # One line, so blank lines in an exception cannot end the HTML block.
                detail = html.escape(entry.detail, quote=False)
                yield f"  <details><summary>{summary}</summary>{detail}</details>"

    def _section(self, key: str, items: Iterable[str]) -> list[str]:
        body = list(items)
        return [f"## {self._catalog.text(key)}", *body, ""] if body else []

    def describe(self, note: ConversionNote) -> str:
        """A note in words: its sentence, then its items (at most NOTE_ITEMS, then "and N more")."""
        shown = []
        for item in note.items[:NOTE_ITEMS]:
            subject = _code(item.subject)
            shown.append(
                f"{subject} ({self._catalog.text(f'note.reason.{item.reason}')})"
                if item.reason
                else subject
            )
        listed = ", ".join(shown)
        hidden = len(note.items) - NOTE_ITEMS
        if hidden > 0:
            listed += self._catalog.text("note.and_more", count=hidden)
        return self._catalog.text(note.kind.key, items=listed)
