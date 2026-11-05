"""The golden outputs of refactor R01 (ADR-0039): every fixture corpus converted by the CLI in each
mode, one SHA-256 per output file. The refactor must leave them byte-identical.

    uv run python tests/support/golden.py   # rewrite tests/golden/manifest.txt (on purpose only)
"""

import hashlib
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tests" / "golden" / "manifest.txt"
CORPORA = ("documents", "html", "odt", "tex")
MODES = {"plain": [], "images": ["--images"], "article": ["--html", "article"]}


def outputs() -> list[str]:
    """The manifest's lines: ``<sha256>  <corpus>/<mode>/<output path>`` (summaries left out:
    they carry the run's date)."""
    from clearmd.frontend.cli import main

    lines: list[str] = []
    for corpus in CORPORA:
        for mode, flags in MODES.items():
            if mode == "article" and corpus != "html":
                continue
            with tempfile.TemporaryDirectory() as temp:
                work, out = Path(temp) / corpus, Path(temp) / "out"
                source = ROOT / "tests" / "fixtures" / corpus
                shutil.copytree(source, work, ignore=shutil.ignore_patterns("__pycache__"))
                main([str(work), "--quiet", "--overwrite", "--output-root", str(out), *flags])
                for path in sorted(p for p in out.rglob("*") if p.is_file()):
                    if not path.name.startswith("Resumen_ClearMD"):
                        digest = hashlib.sha256(path.read_bytes()).hexdigest()
                        name = path.relative_to(out).as_posix()
                        lines.append(f"{digest}  {corpus}/{mode}/{name}")
    return lines


if __name__ == "__main__":
    MANIFEST.write_text("\n".join(outputs()) + "\n", encoding="utf-8")
    print(f"{MANIFEST.relative_to(ROOT)}: written")
    sys.exit(0)
