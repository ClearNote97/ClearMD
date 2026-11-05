"""The size rule (ADR-0039): ≤ 200 lines per file, 250 at most, the tolerance not abused; classes
≤ 150 lines; no mixins of ClearMD's own classes; small entry files. While refactor R01 runs, what
was over the rule is listed in ``size_ratchet`` and may only shrink."""

import ast
from pathlib import Path

from support.size_ratchet import CLASSES, ENTRY_FILES, FILES
from support.source_tree import ROOT, Measured, measured, python_files

TARGET, LIMIT = 200, 250
BAND_SHARE = 0.10  # at most this share of the files between TARGET and LIMIT
CLASS_LIMIT = 150
ENTRY_LIMIT = 40
FILES_NOW = measured()


def _ratchet(sizes: dict[str, int], frozen: dict[str, int], limit: int, what: str) -> list[str]:
    problems = [
        f"{key}: {size} lines (> {limit}); split it" if key not in frozen
        else f"{key}: grew to {size} lines (was {frozen[key]}); it may only shrink"
        for key, size in sizes.items()
        if size > limit and size > frozen.get(key, limit)
    ]  # fmt: skip
    for key, was in frozen.items():
        if sizes.get(key, 0) <= limit:
            problems.append(f"{key}: now within the rule (was {was}); remove it from {what}")
    return problems


def test_no_file_is_over_the_limit() -> None:
    sizes = {file.path: file.lines for file in FILES_NOW}
    assert _ratchet(sizes, FILES, LIMIT, "support.size_ratchet.FILES") == []


def test_the_tolerance_is_not_abused() -> None:
    band = [file.path for file in FILES_NOW if TARGET < file.lines <= LIMIT]
    assert len(band) <= BAND_SHARE * len(FILES_NOW), sorted(band)


def test_no_class_is_over_the_limit() -> None:
    sizes = {f"{f.path}::{name}": n for f in FILES_NOW for name, n in f.classes.items()}
    assert _ratchet(sizes, CLASSES, CLASS_LIMIT, "support.size_ratchet.CLASSES") == []


def test_no_class_mixes_in_another_of_clearmds() -> None:
    own = {name for f in FILES_NOW if f.path.startswith("src/") for name in f.classes}
    mixed = [
        f"{f.path}::{name}{bases}"
        for f in FILES_NOW
        for name, bases in f.bases.items()
        if len(bases) > 1 and any(base.rsplit(".", 1)[-1] in own for base in bases)
    ]
    assert mixed == []


def test_each_interface_starts_from_a_small_entry_file() -> None:
    entries = {f.path: f.lines for f in FILES_NOW if _is_entry(f)}  # frontend/<interface>/app.py
    assert entries, "no entry file found: the measure is wrong"
    assert _ratchet(entries, ENTRY_FILES, ENTRY_LIMIT, "support.size_ratchet.ENTRY_FILES") == []


def test_every_source_module_says_what_it_is() -> None:
    silent = [
        f.path
        for f in FILES_NOW
        if f.path.startswith("src/")
        and ast.get_docstring(ast.parse((ROOT / f.path).read_text(encoding="utf-8"))) is None
    ]
    assert silent == []


def test_the_measure_reaches_every_subpackage() -> None:
    found = {path.relative_to(ROOT).as_posix() for path in python_files()}
    deepest = max(found, key=lambda path: path.count("/"))
    assert deepest.count("/") >= 6, deepest  # src/clearmd/backend/services/conversion/pdf/…
    assert all(Path(ROOT / path).is_file() for path in list(FILES) + list(ENTRY_FILES))


def _is_entry(file: Measured) -> bool:
    parts = file.path.split("/")
    return parts[:3] == ["src", "clearmd", "frontend"] and len(parts) == 5 and parts[4] == "app.py"
