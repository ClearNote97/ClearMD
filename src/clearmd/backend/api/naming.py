"""Names that depend on the user's language: a split file's parts (feature 023) and a merged
file (feature 026)."""

from dataclasses import replace

from clearmd.backend.schemas.models import BatchPlan
from clearmd.i18n import load_catalog

STAMP = "%Y-%m-%d %H-%M"  # a merged file's time: sorts right, and a valid file name everywhere


def named(plan: BatchPlan, language: str) -> BatchPlan:
    return _merge_named(_parts_named(plan, language), language)


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


def _merge_named(plan: BatchPlan, language: str) -> BatchPlan:
    """The merged file named in the user's language: "Merged 2026-11-08 10-30.md"."""
    merge = plan.merge
    if merge is None or not plan.conversions:
        return plan
    catalog = load_catalog(language)
    name = catalog.text("merge.name", stamp=merge.stamp)
    target = merge.target.with_name(name + merge.target.suffix)
    return replace(
        plan,
        conversions=tuple(replace(item, target=target) for item in plan.conversions),
        merge=replace(merge, target=target, heading=catalog.text_template("merge.heading")),
    )
