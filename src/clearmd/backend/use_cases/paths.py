"""Pure output-path rules (ADR-0016). Folders, root/home and collisions are completed in T11."""

from pathlib import Path

from clearmd.backend.schemas.formats import OUTPUT_DIR_NAME, RESULTS_DIR_NAME


def output_root_for(source: Path, *, is_dir: bool, override: Path | None = None) -> Path:
    """``<output parent>/ClearMD_Output`` for an input file or folder."""
    parent = override if override is not None else source.parent
    return parent / OUTPUT_DIR_NAME


def target_for(source: Path, output_root: Path, relative_dir: Path = Path()) -> Path:
    """Where the Markdown of ``source`` goes: ``Output/<relative_dir>/<full stem>.md``."""
    return output_root / RESULTS_DIR_NAME / relative_dir / f"{source.stem}.md"
