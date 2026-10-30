"""ClearMD's own content signatures (feature 010) on the fixtures magika recognized (001)."""

import shutil
from pathlib import Path

import pytest
from support import DOCUMENTS_DIR

from clearmd.backend.schemas.formats import FormatId, format_for_extension
from clearmd.backend.schemas.models import DetectionMethod
from clearmd.backend.services.detection.content import SignatureDetector


@pytest.fixture(scope="module")
def detector() -> SignatureDetector:
    return SignatureDetector()


SAMPLES = sorted(p.name for p in DOCUMENTS_DIR.glob("sample.*"))


@pytest.mark.parametrize("name", SAMPLES)
def test_every_supported_format_is_recognized_by_content(
    detector: SignatureDetector, name: str
) -> None:
    detection = detector.detect(DOCUMENTS_DIR / name)
    assert detection is not None
    assert detection.format is format_for_extension(Path(name).suffix)
    assert detection.method is DetectionMethod.CONTENT


def test_a_docx_without_extension_is_a_docx(detector: SignatureDetector) -> None:
    detection = detector.detect(DOCUMENTS_DIR / "docx_without_extension")
    assert detection is not None and detection.format is FormatId.DOCX


def test_text_with_an_unknown_extension_is_plain_text(
    detector: SignatureDetector, tmp_path: Path
) -> None:
    path = tmp_path / "notes.dat"
    shutil.copyfile(DOCUMENTS_DIR / "sample.txt", path)
    detection = detector.detect(path)
    assert detection is not None and detection.format is FormatId.TXT


def test_unrecognized_content_is_not_detected(detector: SignatureDetector, tmp_path: Path) -> None:
    assert detector.detect(DOCUMENTS_DIR / "corrupt.pdf") is None
    script = tmp_path / "tool"
    script.write_text("import sys\n\ndef main():\n    print(sys.argv)\n", encoding="utf-8")
    assert detector.detect(script) is None


def test_odt_without_extension_is_detected_by_content(detector: SignatureDetector) -> None:
    from support import ODT_DIR

    detection = detector.detect(ODT_DIR / "no_extension_odt")
    assert detection is not None and detection.format is FormatId.ODT


def test_latex_without_extension_is_detected_by_content(detector: SignatureDetector) -> None:
    from support import TEX_DIR

    detection = detector.detect(TEX_DIR / "no_extension_latex")
    assert detection is not None and detection.format is FormatId.TEX


# --- Code review and security audit of 010 (C10-*, S10-*) ------------------------------------


def _detect(tmp_path: Path, content: str | bytes) -> FormatId | None:
    from clearmd.backend.services.detection.content import detect_format

    path = tmp_path / "unnamed"
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_bytes(content)
    return detect_format(path)


def test_c10_1_a_large_notebook_is_a_notebook(tmp_path: Path) -> None:
    image = "A" * 120_000
    notebook = (
        '{\n "cells": [\n  {\n   "cell_type": "code",\n   "outputs": [{"data": {"image/png": "'
        + image + '"}}],\n   "source": ["print(1)"]\n  }\n ],\n "metadata": {},\n "nbformat": 4\n}'
    )  # fmt: skip
    assert _detect(tmp_path, notebook) is FormatId.IPYNB


@pytest.mark.parametrize(
    "content",
    [
        "2026-10-29 10:00:01 INFO start\n2026-10-29 10:00:02 INFO, user=1\n",
        "const a = 1;\nconst b = 2;\nconst c = 3;\nconsole.log(a, b, c);\n",
        "| a | b |\n|---|---|\n| 1 | 2 |\n",
        "Hello, world.\nThis, too.\n",
        "a;b;c\n1;2;3\n4;5;6\n",
    ],
)
def test_c10_3_only_real_comma_separated_rows_are_csv(tmp_path: Path, content: str) -> None:
    assert _detect(tmp_path, content) is not FormatId.CSV


def test_c10_3_a_real_csv_still_is(tmp_path: Path) -> None:
    assert _detect(tmp_path, "name,value\nalpha,1\nbeta,2\ngamma,3\n") is FormatId.CSV


@pytest.mark.parametrize(
    "program",
    [
        'title = "\\\\section{Intro}"\nimport os\n',  # mentions LaTeX: still a program
        '#include "stdio.h"\nint main(void) { return 0; }\n',
        "<?php echo 'hi'; ?>\n",
        "const fs = require('fs');\nmodule.exports = {};\n",
        'if __name__ == "__main__":\n    main()\n',
    ],
)
def test_c10_4_c10_5_programs_are_unsupported(tmp_path: Path, program: str) -> None:
    assert _detect(tmp_path, program) is None


def test_c10_5_a_readme_with_a_code_example_is_text(tmp_path: Path) -> None:
    readme = "# Tool\n\nInstall it, then:\n\n```python\nimport tool\n```\n\nThat is all.\n"
    assert _detect(tmp_path, readme) is FormatId.TXT


@pytest.mark.parametrize(
    "page",
    [
        '<?xml version="1.0"?>\n<!DOCTYPE html>\n<html><body>x</body></html>',
        "<!-- a -->\n<!-- b -->\n<html><body>x</body></html>",
        "<body><p>x</p></body>",
    ],
)
def test_c10_6_xhtml_comments_and_body_fragments_are_html(tmp_path: Path, page: str) -> None:
    assert _detect(tmp_path, page) is FormatId.HTML


def test_s10_1_many_comments_never_stall_detection(tmp_path: Path) -> None:
    import time

    start = time.perf_counter()
    _detect(tmp_path, "<!---->" * 5000 + "x")
    assert time.perf_counter() - start < 1


def test_s10_3_a_compressed_mimetype_is_never_read(tmp_path: Path) -> None:
    import zipfile

    path = tmp_path / "unnamed"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", b"application/epub+zip", compress_type=zipfile.ZIP_BZIP2)
    from clearmd.backend.services.detection.content import detect_format

    assert detect_format(path) is None


def test_s10_4_a_huge_zip_index_is_refused_before_it_is_read(tmp_path: Path) -> None:
    import zipfile

    path = tmp_path / "unnamed"
    with zipfile.ZipFile(path, "w") as archive:
        for index in range(60_000):
            archive.writestr(str(index), b"")
    from clearmd.backend.services.detection.content import detect_format

    assert detect_format(path) is None


def test_s10_5_deep_json_or_an_encrypted_entry_is_unsupported_not_an_error(
    tmp_path: Path,
) -> None:
    assert _detect(tmp_path, '{"cells": [{"cell_type": ' + "[" * 60_000) in {None, FormatId.TXT}


@pytest.mark.parametrize("start", ["<header>x</header>", "<bodyguard>x</bodyguard>"])
def test_a10_6_a_tag_that_only_begins_like_html_is_no_page(tmp_path: Path, start: str) -> None:
    assert _detect(tmp_path, start) is not FormatId.HTML
