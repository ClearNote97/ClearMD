"""The benchmark cases: which generator, extension, sizes and engine per kind."""

import random
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from benchlib.odt import make_odt
from benchlib.office import make_docx_images, make_docx_text, make_epub, make_pptx, make_xlsx
from benchlib.pdf import make_pdf
from benchlib.tex import make_tex, make_tex_macros
from benchlib.text import make_csv, make_html, make_html_article, make_ipynb, make_txt


@dataclass(frozen=True)
class Case:
    kind: str
    extension: str
    build: Callable[[Path, int, random.Random], None]
    sizes_mib: tuple[float, ...]
    engine: str = "markitdown"  # or "tex" / "odt" / "article": ClearMD's own (002, 003, 004)


CASES = [
    Case("txt", ".txt", make_txt, (1, 10, 50, 100)),
    Case("csv", ".csv", make_csv, (1, 10, 50, 100)),
    Case("html", ".html", make_html, (1, 10, 50)),
    Case("ipynb", ".ipynb", make_ipynb, (1, 10, 50)),
    Case("pdf", ".pdf", make_pdf, (1, 5, 20)),
    Case("docx_text", ".docx", make_docx_text, (1, 10, 50)),
    Case("docx_images", ".docx", make_docx_images, (10, 50, 100)),
    Case("epub", ".epub", make_epub, (1, 10, 50)),
    Case("pptx", ".pptx", make_pptx, (1, 10)),
    Case("xlsx", ".xlsx", make_xlsx, (1, 10, 50)),
    Case("tex", ".tex", make_tex, (1, 5, 10, 25), "tex"),
    Case("tex_macros", ".tex", make_tex_macros, (1, 5, 10, 25), "tex"),
    Case("odt", ".odt", make_odt, (1, 5, 10, 25), "odt"),
    Case("html_article", ".html", make_html_article, (1, 5, 10, 25), "article"),
]
