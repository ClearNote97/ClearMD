"""A split file's parts: their names, and the parts of an earlier cut (features 023, 027)."""

import os
import re
from pathlib import Path

from clearmd.backend.schemas.formats import PART_NAMES
from clearmd.backend.schemas.models import PlannedConversion
from clearmd.backend.schemas.split import SplitSpec


def part_name(spec: SplitSpec, name: str, index: int, total: int) -> str:
    """A part's name without extension; the index padded to the total's width (sorts right)."""
    width = len(str(total))
    return spec.part_name.format(name=name, index=str(index).zfill(width), total=total)


def _earlier_part(spec: SplitSpec, name: str) -> re.Pattern[str]:
    """Any part of an earlier cut of ``name``, in any language ClearMD speaks (audit v2, B3-04):
    ClearMD's own names only."""
    patterns = []
    for template in dict.fromkeys((spec.part_name, *PART_NAMES)):
        pattern = re.escape(template)
        for field, value in (("name", re.escape(name)), ("index", r"\d+"), ("total", r"\d+")):
            pattern = pattern.replace(re.escape("{" + field + "}"), value)
        patterns.append(pattern)
    return re.compile("(?:" + "|".join(patterns) + r")\.(?:pdf|md|txt|csv|xlsx)")


def earlier_parts(item: PlannedConversion, spec: SplitSpec) -> list[Path]:
    """The parts an earlier cut of this file left in its folder (ClearMD's own names only)."""
    return parts_in(item.target, spec)


def parts_in(folder: Path, spec: SplitSpec) -> list[Path]:
    """ClearMD's own parts in ``folder``: what makes a Split's folder a result (audit v3, B1-02).
    An empty folder, or one with only other files, is not one."""
    if not os.path.isdir(folder) or os.path.islink(folder):
        return []
    own = _earlier_part(spec, folder.name)
    with os.scandir(folder) as entries:
        return [Path(entry.path) for entry in entries if own.fullmatch(entry.name)]


def has_result(item: PlannedConversion) -> bool:
    """Whether ``item`` already has a result: its file, or, for Split, its own parts."""
    if item.split is None:
        return item.target.exists()
    return bool(parts_in(item.target, item.split))
