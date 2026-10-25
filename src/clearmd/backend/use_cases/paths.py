"""Pure output-path rules (ADR-0016, ADR-0019)."""

import os
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from clearmd.backend.schemas.formats import OUTPUT_DIR_NAME, RESULTS_DIR_NAME


def keeps_output_inside(folder: Path) -> bool:
    """A drive root or the user's home has no useful parent: its ClearMD_Output goes inside it."""
    return folder == folder.parent or folder == Path(os.path.abspath(Path.home()))


def output_parent_for(source: Path, *, is_dir: bool, override: Path | None = None) -> Path:
    if override is not None:
        return override
    if is_dir and keeps_output_inside(source):
        return source
    return source.parent


def output_root_for(source: Path, *, is_dir: bool, override: Path | None = None) -> Path:
    """``<output parent>/ClearMD_Output`` for an input file or folder."""
    return output_parent_for(source, is_dir=is_dir, override=override) / OUTPUT_DIR_NAME


def target_for(source: Path, output_root: Path, relative_dir: Path = Path()) -> Path:
    """Where the Markdown of ``source`` goes: ``OutputMD/<relative_dir>/<full stem>.md``."""
    return output_root / RESULTS_DIR_NAME / relative_dir / f"{source.stem}.md"


@dataclass(frozen=True)
class NameRequest:
    source: Path
    target: Path
    # Shown in a collision suffix: the source extension, or the detected format without one.
    label: str


def _key(path: Path) -> str:
    return str(path).casefold()


def _with_label(target: Path, label: str) -> Path:
    return target.with_name(f"{target.stem} ({label}){target.suffix}")


def resolve_names(requests: Sequence[NameRequest]) -> list[Path]:
    """Final targets, unique case-insensitively, independent of the order of ``requests``.

    Targets that do not collide keep their name. Colliding ones all get ``(label)``; if that is
    taken, ``(label N)`` with N = 2, 3... in path order.
    """
    order = sorted(
        range(len(requests)),
        key=lambda i: (_key(requests[i].source), str(requests[i].source)),
    )
    counts = Counter(_key(request.target) for request in requests)
    final: list[Path | None] = [None] * len(requests)
    taken: set[str] = set()
    for i in order:
        if counts[_key(requests[i].target)] == 1:
            final[i] = requests[i].target
            taken.add(_key(requests[i].target))
    for i in order:
        if final[i] is not None:
            continue
        request = requests[i]
        number = 1
        candidate = _with_label(request.target, request.label)
        while _key(candidate) in taken:
            number += 1
            candidate = _with_label(request.target, f"{request.label} {number}")
        final[i] = candidate
        taken.add(_key(candidate))
    return [path for path in final if path is not None]
