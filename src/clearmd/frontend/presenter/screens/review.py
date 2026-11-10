"""Review: the plan's rows, summary and figures."""

from collections.abc import Sequence
from pathlib import Path

from clearmd.backend.api import Strategy, large_in_plan, skip_action, skip_reason
from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.models import BatchPlan, PlannedConversion, SkippedItem
from clearmd.frontend.presenter.icons import icon_for, icon_of_format
from clearmd.frontend.presenter.models import PlanRow, PlanView, RowKind, Stat, Tone
from clearmd.frontend.presenter.screens.choose import shown
from clearmd.i18n import Catalog


def plan_view(catalog: Catalog, plan: BatchPlan, on_existing_output: str, plan_id: int) -> PlanView:
    rows: list[PlanRow] = []
    for item in plan.conversions:
        kind = RowKind.EXISTS if item.exists else RowKind.CONVERT
        icon = icon_of_format(item.detection.format)
        name, location = shown(item.source)
        key = "gui.plan.exists" if item.exists else "gui.plan.ready"
        detail = catalog.text(key, format=format_of(catalog, item) + _cut(catalog, item))
        rows.append(PlanRow(kind, name, location, detail, icon))
    for skipped in plan.skipped:
        reason = skip_reason(catalog, skipped)
        word = catalog.text("gui.result.word_skipped")  # a word, never a colour alone (F2-05)
        detail = f"{word} {reason}. {skip_action(catalog, skipped)}"
        name, location = shown(skipped.path, is_dir=skipped.is_dir)
        icon = icon_for(skipped.path, is_folder=skipped.is_dir)
        rows.append(PlanRow(RowKind.SKIPPED, name, location, detail, icon))
    for missing in plan.input_errors:
        detail = f"{catalog.text('gui.plan.word_missing')} {catalog.text('gui.plan.not_found')}"
        name, location = shown(missing.path)
        icon = icon_for(missing.path, is_folder=False)  # it is not there: only its name
        rows.append(PlanRow(RowKind.MISSING, name, location, detail, icon))
    existing = len(plan.existing)
    new = len(plan.conversions) - existing  # each file counted once (audit v3, F5-01)
    summary = catalog.text(
        "gui.plan.summary",
        convert=new,
        skipped=len(plan.skipped) + len(plan.input_errors),
        existing=existing,
    )
    asks = existing > 0 and on_existing_output == "ask"
    stats = (
        stat(catalog, "gui.plan.stat_convert", new, Tone.ACCENT),
        stat(
            catalog,
            "gui.plan.stat_skipped",
            len(plan.skipped) + len(plan.input_errors),
            Tone.WARNING if plan.input_errors else skipped_tone(plan.skipped),
        ),
        stat(catalog, "gui.plan.stat_existing", existing, Tone.NEUTRAL),
    )
    return PlanView(
        summary, tuple(rows), asks, stats, plan_id, split_offer(catalog, large_in_plan(plan))
    )


# Left out because nothing had to be done: no colour of alarm (audit v3, F5-02).
INFORMING = frozenset(
    {
        SkipReason.ALREADY_MARKDOWN,
        SkipReason.ALREADY_INCLUDED,
        SkipReason.LOCK_FILE,
        SkipReason.HIDDEN,
        SkipReason.OUTPUT_FOLDER,
        SkipReason.EXISTING_OUTPUT,
    }
)


def skipped_tone(skipped: Sequence[SkippedItem]) -> Tone:
    """Amber only when a left-out file asks something of the person (audit v4, F5-04)."""
    return Tone.WARNING if any(s.reason not in INFORMING for s in skipped) else Tone.NEUTRAL


def split_offer(catalog: Catalog, found: tuple[tuple[Path, int], ...]) -> str:
    """The action that splits the PDFs too large to convert (feature 025); "" when none."""
    return catalog.text("gui.offer.split", count=len(found)) if found else ""


def stat(catalog: Catalog, key: str, value: int, tone: Tone = Tone.WARNING) -> Stat:
    """A figure; a warning or a problem only when it is not zero. One is said in the singular
    ("1 Omitido") where the language has its own word (audit v3, F5-07)."""
    one = f"{key}_one"
    label = catalog.text(one) if value == 1 and one in catalog.keys() else catalog.text(key)
    return Stat(label, value, tone if value or tone is Tone.ACCENT else Tone.NEUTRAL)


def _cut(catalog: Catalog, item: PlannedConversion) -> str:
    """How a file will be split (feature 023): " · into 4 parts"; nothing for Convert."""
    if item.split is None:
        return ""  # Convert, and Merge (its order is the list's; the row says it)
    key = f"gui.split.by_{item.split.cut.value}"  # by_parts, by_pages, by_words
    return " · " + catalog.text(key, count=item.split.size)


def format_of(catalog: Catalog, item: PlannedConversion) -> str:
    text = item.detection.format.value.upper()
    if item.strategy is not Strategy.FULL:
        text = catalog.text(f"summary.strategy.{item.strategy.value}", format=text)
    return text
