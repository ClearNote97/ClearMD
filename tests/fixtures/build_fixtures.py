"""Build the sample documents used by the tests, reproducibly.

Run inside the container:  uv run python tests/fixtures/build_fixtures.py

Every document carries a unique marker (``MARKERS``) so a test can check that its text survived the
conversion. ZIP-based documents get fixed timestamps, so rebuilding yields the same bytes. The
builders live in ``builders/``, one module per format.
"""

from pathlib import Path

from builders.common import DOCUMENTS_DIR
from builders.documents import build
from builders.html import HTML_DIR, build_html
from builders.odt import ODT_DIR, build_odt
from builders.tex import TEX_DIR, build_tex

if __name__ == "__main__":
    built = [
        *build(DOCUMENTS_DIR).values(),
        *build_tex(TEX_DIR).values(),
        *build_odt(ODT_DIR).values(),
        *build_html(HTML_DIR).values(),
    ]
    for path in built:
        shown = path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path
        print(f"{path.stat().st_size:>8}  {shown}")
