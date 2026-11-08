"""A split file's parts: their names, and the parts of an earlier cut (features 023, 027)."""

import os
import re
from pathlib import Path

from clearmd.backend.schemas.models import PlannedConversion
from clearmd.backend.schemas.split import SplitSpec
from clearmd.backend.use_cases.output_files import remove_regular_file


def part_name(spec: SplitSpec, name: str, index: int, total: int) -> str:
    """A part's name without extension; the index padded to the total's width (sorts right)."""
    width = len(str(total))
    return spec.part_name.format(name=name, index=str(index).zfill(width), total=total)


def _earlier_part(spec: SplitSpec, name: str) -> re.Pattern[str]:
    """Any part of an earlier cut of ``name``: ClearMD's own names only."""
    pattern = re.escape(spec.part_name)
    for field, value in (("name", re.escape(name)), ("index", r"\d+"), ("total", r"\d+")):
        pattern = pattern.replace(re.escape("{" + field + "}"), value)
    return re.compile(pattern + r"\.(?:pdf|md|txt|csv|xlsx)")


def remove_earlier_parts(item: PlannedConversion, spec: SplitSpec) -> None:
    folder = item.target
    if not os.path.isdir(folder) or os.path.islink(folder):
        return
    own = _earlier_part(spec, item.target.name)
    with os.scandir(folder) as entries:
        old = [Path(entry.path) for entry in entries if own.fullmatch(entry.name)]
    for path in old:
        remove_regular_file(path, inside=item.output_root)
