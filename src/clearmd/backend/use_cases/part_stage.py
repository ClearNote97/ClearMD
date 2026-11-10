"""A split's parts are written aside and put in place together (audit 2026-11-08, B1-01).

An earlier cut is removed only once every new part is written: a failure, a time limit or a
cancel halfway leaves the earlier parts as they were. The staged names start with a dot and
carry ``.clearmd-part``, so the start-up sweep removes any a power cut leaves behind.
"""

import contextlib
import os
from pathlib import Path

from clearmd.backend.schemas.formats import STAGED_MARK
from clearmd.backend.schemas.models import PlannedConversion
from clearmd.backend.schemas.split import SplitSpec
from clearmd.backend.use_cases.output_files import UnsafeOutput, remove_regular_file
from clearmd.backend.use_cases.split_names import earlier_parts


class PartStage:
    """The parts of one split: ``at(final)`` names where to write each, ``commit`` moves them."""

    def __init__(self, item: PlannedConversion, spec: SplitSpec) -> None:
        self._item = item
        self._spec = spec
        self._staged: list[tuple[Path, Path]] = []
        self._dropped: set[Path] = set()  # parts removed on purpose (only their Markdown kept)

    def at(self, final: Path) -> Path:
        """Where to write the part that will be ``final``; its extension stays (the worker
        detects a part by it)."""
        staged = final.with_name(f".{final.stem}{STAGED_MARK}{final.suffix}")
        self._staged.append((staged, final))
        return staged

    def drop(self, staged: Path) -> None:
        """A staged part removed on purpose: only its Markdown is kept."""
        self._dropped.add(staged)

    def commit(self) -> None:
        """Every part in place, then the earlier cut's other parts removed."""
        for _staged, final in self._staged:  # an obstacle stops it before anything moves
            if os.path.lexists(final) and (os.path.islink(final) or not os.path.isfile(final)):
                raise UnsafeOutput(f"not a regular file: {final}")
        old = earlier_parts(self._item, self._spec)
        finals = set()
        missing = [staged for staged, _ in self._staged if not os.path.lexists(staged)]
        missing = [path for path in missing if path not in self._dropped]
        if missing:  # gone without ClearMD removing it: never "split" with parts missing (B1-01)
            raise OSError(f"{len(missing)} prepared parts disappeared before they were moved")
        for staged, final in self._staged:
            if os.path.lexists(staged):  # a part's original removed after its Markdown: gone
                os.replace(staged, final)
                finals.add(final)
        for path in old:
            if path not in finals:
                remove_regular_file(path, inside=self._item.output_root)
        self._staged.clear()

    def discard(self) -> None:
        """The new parts removed; the earlier cut untouched."""
        for staged, _final in self._staged:
            with contextlib.suppress(OSError):
                remove_regular_file(staged, inside=self._item.output_root)
        self._staged.clear()
