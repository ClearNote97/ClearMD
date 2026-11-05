"""Signatures of text formats: is a sample HTML, a notebook, TeX, a program or CSV.

Pure functions of the first 64 KiB decoded as text; the order they are tried in is
``content.detect_format``'s. Every check is linear in the sample (no regular expression that
can backtrack, security audit of 010).
"""

import csv
import io
import json
import re

MAX_COMMENTS = 100  # comments before an HTML page's first tag
MIN_CSV_LINES = 3

HTML_STARTS = ("<!doctype html", "<html", "<head", "<body")
TAG_ENDS = (" ", ">", "\n", "\t", "\r", "/")
NOTEBOOK = re.compile(r'\A\s*\{\s*"cells"\s*:\s*\[')  # nbformat writes its keys sorted
TEX = re.compile(r"\\(?:documentclass|begin\{document\})")
TEX_COMMANDS = re.compile(r"\\(?:section|subsection|chapter|begin|usepackage)\*?\{")
# A program, not a document: lines a script or a source file starts with (a fenced block of a
# README is left out first).
CODE = re.compile(
    r"\A#!|^(?:import \w|from [\w.]+ import |def \w+\(|class \w+[(:]|#include\s*[<\"]|<\?php|"
    r"package [\w.]+;?$|public (?:static )?(?:class|void)|function \w+\(|"
    r"(?:const|let|var) \w+ = require\(|module\.exports|if __name__ == )",
    re.MULTILINE,
)
BOMS = ((b"\xef\xbb\xbf", "utf-8"), (b"\xff\xfe", "utf-16-le"), (b"\xfe\xff", "utf-16-be"))


def as_text(sample: bytes) -> str | None:
    """The sample as text, or None for binary data (a NUL, or bytes no text encoding makes)."""
    for bom, encoding in BOMS:
        if sample.startswith(bom):
            return sample[len(bom) :].decode(encoding, errors="ignore")
    if b"\x00" in sample:
        return None
    try:
        return sample.decode("utf-8")
    except UnicodeDecodeError as error:
        if error.start >= len(sample) - 3:  # the sample cut a character in two
            return sample[: error.start].decode("utf-8")
    text = sample.decode("latin-1")
    controls = sum(1 for char in text if ord(char) < 0x20 and char not in "\t\n\r\f")
    return text if controls <= len(text) // 100 else None


def without_fences(text: str) -> str:
    """The text without its fenced blocks (a README's code examples), line by line."""
    kept: list[str] = []
    fence = ""
    for line in text.split("\n"):
        marker = line.lstrip()[:3]
        if marker in ("```", "~~~") and (not fence or marker == fence):
            fence = "" if fence else marker
        elif not fence:
            kept.append(line)
    return "\n".join(kept)


def is_html(text: str) -> bool:
    """A page: past an XML declaration and its comments, a doctype or an html, head or body."""
    rest = text.lstrip()
    if rest.startswith("<?xml"):
        rest = rest[rest.find("?>") + 2 :].lstrip() if "?>" in rest else ""
    for _ in range(MAX_COMMENTS):
        if not rest.startswith("<!--"):
            break
        end = rest.find("-->")
        if end < 0:
            return False
        rest = rest[end + 3 :].lstrip()
    lowered = rest[:16].lower()
    for start in HTML_STARTS:
        # The tag's name ends there: "<header>" or "<bodyguard>" is not a page (adversarial check).
        boundary = lowered[len(start) : len(start) + 1]
        if lowered.startswith(start) and boundary in TAG_ENDS:
            return True
    return False


def is_notebook(text: str, cut: bool) -> bool:
    if not NOTEBOOK.match(text) or '"cell_type"' not in text:
        return False
    if cut:  # a notebook with images is far larger than the sample: its start is enough
        return True
    try:
        notebook = json.loads(text)
    except (ValueError, RecursionError):
        return False
    return isinstance(notebook, dict) and "nbformat" in notebook


def is_csv(text: str, cut: bool) -> bool:
    """Comma-separated rows (the only separator the converter reads), at least three, each with
    the same number of fields; not a Markdown table, not code."""
    lines = [line for line in text.splitlines() if line.strip()]
    if cut:
        lines = lines[:-1]  # the last line may be cut in two
    lines = lines[:50]
    if len(lines) < MIN_CSV_LINES:
        return False
    if any(
        line.lstrip().startswith("|") or line.rstrip().endswith((";", "{", "}")) for line in lines
    ):
        return False
    try:
        rows = list(csv.reader(io.StringIO("\n".join(lines))))
    except csv.Error:
        return False
    widths = {len(row) for row in rows}
    return len(widths) == 1 and widths.pop() >= 2
