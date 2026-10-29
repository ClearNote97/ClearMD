"""The summary of a real batch, in both languages, for the docs (feature 009): the Markdown as
written, the PDF and a picture of its first page. Only the fixtures are converted.

Run in the dev container: ``uv run python tests/gui/summary_samples.py --out docs/screenshots/009``.
"""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

import pypdfium2 as pdfium

from clearmd.frontend.cli import main as clearmd

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "documents"
BATCH = {
    "report.docx": "sample.docx",
    "notes.txt": "sample.txt",
    "thesis/chapter.pdf": "sample.pdf",
    "thesis/locked.pdf": "encrypted.pdf",
    "slides.pptx": "sample.pptx",
    "broken.docx": "corrupt.docx",
    "readme.md": "sample.txt",
}


def sample(language: str, out: Path) -> None:
    with tempfile.TemporaryDirectory() as folder:
        docs = Path(folder) / "Documents"
        for name, fixture in BATCH.items():
            (docs / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(FIXTURES / fixture, docs / name)
        clearmd([str(docs), "--quiet", "--summary-pdf", "--lang", language])
        results = Path(folder) / "ClearMD_Output"
        shutil.copyfile(results / "Resumen_ClearMD.md", out / f"summary-{language}.md")
        shutil.copyfile(results / "Resumen_ClearMD.pdf", out / f"summary-{language}.pdf")
        document = pdfium.PdfDocument(str(results / "Resumen_ClearMD.pdf"))
        document[0].render(scale=1.6).to_pil().save(out / f"summary-pdf-{language}.png")
        document.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Sample summaries for the docs")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for language in ("en", "es"):
        sample(language, args.out)
        print(args.out / f"summary-pdf-{language}.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
