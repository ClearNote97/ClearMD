"""The LaTeX fixtures (feature 002)."""

from pathlib import Path

from builders.png import tiny_png
from builders.tex_sources import (
    HOSTILE,
    LATIN1_DECLARED,
    LATIN1_UNDECLARED,
    MALFORMED_TEX,
    MULTICOLUMN_TEX,
    PAPER_TEX,
    THESIS_CH1,
    THESIS_CH2,
    THESIS_DEEPER,
    THESIS_MACROS,
    THESIS_MAIN,
    UNKNOWN_TEX,
)

TEX_DIR = Path(__file__).parent.parent / "tex"


def build_tex(destination: Path) -> dict[str, Path]:
    """Write the LaTeX fixtures (relative names, folders included) and return them."""
    files: dict[str, bytes] = {
        "paper.tex": PAPER_TEX.encode(),
        "img/plot.png": tiny_png(),
        "unknown.tex": UNKNOWN_TEX.encode(),
        "multicolumn.tex": MULTICOLUMN_TEX.encode(),
        "malformed.tex": MALFORMED_TEX.encode(),
        "latin1.tex": LATIN1_DECLARED.encode("latin-1"),
        "latin1_undeclared.tex": LATIN1_UNDECLARED.encode("latin-1"),
        "no_extension_latex": PAPER_TEX.encode(),
        "thesis/main.tex": THESIS_MAIN.encode(),
        "thesis/macros.tex": THESIS_MACROS.encode(),
        "thesis/chapters/ch1.tex": THESIS_CH1.encode(),
        "thesis/chapters/ch2.tex": THESIS_CH2.encode(),
        "thesis/chapters/sections/deeper.tex": THESIS_DEEPER.encode(),
        "thesis/img/plot.png": tiny_png(),
        **{f"hostile/{name}": text.encode() for name, text in HOSTILE.items()},
    }
    written = {}
    for name, data in files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        written[name] = path
    return written
