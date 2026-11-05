"""Helpers shared by the review-finding regressions of the LaTeX converter."""

from pathlib import Path

from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.tex.render import render_latex


def md(latex: str) -> str:
    return render_latex(latex).markdown


def doc(body: str, preamble: str = "") -> str:
    return f"\\documentclass{{article}}{preamble}\\begin{{document}}{body}\\end{{document}}"


def kinds(latex: str) -> set[NoteKind]:
    return {note.kind for note in render_latex(latex).notes}


def write(folder: Path, name: str, text: str | bytes) -> Path:
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(text, bytes):
        path.write_bytes(text)
    else:
        path.write_text(text, encoding="utf-8")
    return path
