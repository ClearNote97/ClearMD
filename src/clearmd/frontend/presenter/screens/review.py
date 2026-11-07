"""Review: the plan's rows, summary and figures."""

from pathlib import Path

from clearmd.backend.api import Strategy, large_in_plan, skip_action, skip_reason
from clearmd.backend.schemas.models import BatchPlan, PlannedConversion
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
        detail = f"{reason}. {skip_action(catalog, skipped)}"
        name, location = shown(skipped.path, is_dir=skipped.is_dir)
        icon = icon_for(skipped.path, is_folder=skipped.is_dir)
        rows.append(PlanRow(RowKind.SKIPPED, name, location, detail, icon))
    for missing in plan.input_errors:
        detail = catalog.text("gui.plan.not_found")
        name, location = shown(missing.path)
        icon = icon_for(missing.path, is_folder=False)  # it is not there: only its name
        rows.append(PlanRow(RowKind.MISSING, name, location, detail, icon))
    existing = len(plan.existing)
    summary = catalog.text(
        "gui.plan.summary",
        convert=len(plan.conversions),
        skipped=len(plan.skipped) + len(plan.input_errors),
        existing=existing,
    )
    asks = existing > 0 and on_existing_output == "ask"
    stats = (
        stat(catalog, "gui.plan.stat_convert", len(plan.conversions), Tone.ACCENT),
        stat(catalog, "gui.plan.stat_skipped", len(plan.skipped) + len(plan.input_errors)),
        stat(catalog, "gui.plan.stat_existing", existing, Tone.NEUTRAL),
    )
    return PlanView(
        summary, tuple(rows), asks, stats, plan_id, split_offer(catalog, large_in_plan(plan))
    )


def split_offer(catalog: Catalog, found: tuple[tuple[Path, int], ...]) -> str:
    """The action that splits the PDFs too large to convert (feature 025); "" when none."""
    return catalog.text("gui.offer.split", count=len(found)) if found else ""


def stat(catalog: Catalog, key: str, value: int, tone: Tone = Tone.WARNING) -> Stat:
    """A figure; a warning or a problem only when it is not zero."""
    return Stat(catalog.text(key), value, tone if value or tone is Tone.ACCENT else Tone.NEUTRAL)


def _cut(catalog: Catalog, item: PlannedConversion) -> str:
    """How a file will be split (feature 023): " · into 4 parts"; nothing for Convert."""
    if item.split is None:
        return ""
    key = f"gui.split.by_{item.split.cut.value}"  # by_parts, by_pages, by_words
    return " · " + catalog.text(key, count=item.split.size)


def format_of(catalog: Catalog, item: PlannedConversion) -> str:
    text = item.detection.format.value.upper()
    if item.strategy is not Strategy.FULL:
        text = catalog.text(f"summary.strategy.{item.strategy.value}", format=text)
    return text
