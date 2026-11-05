"""Generators of the plain-text formats: txt, csv, html (and article mode) and ipynb."""

import json
import random
from pathlib import Path
from typing import Any

from benchlib.common import _line, _words


def make_txt(path: Path, size: int, rng: random.Random) -> None:
    with path.open("w", encoding="utf-8") as out:
        while out.tell() < size:
            out.write(_line(rng) + "\n")


def make_csv(path: Path, size: int, rng: random.Random) -> None:
    with path.open("w", encoding="utf-8") as out:
        out.write("id,name,value,comment\n")
        row = 0
        while out.tell() < size:
            row += 1
            out.write(f"{row},{_words(rng, 2)},{rng.random() * 1000:.3f},{_words(rng, 6)}\n")


def make_html(path: Path, size: int, rng: random.Random) -> None:
    with path.open("w", encoding="utf-8") as out:
        out.write(
            "<!DOCTYPE html><html><head><meta charset='utf-8'><title>bench</title></head><body>"
        )
        while out.tell() < size:
            out.write(f"<h2>{_words(rng, 3)}</h2><p>{_words(rng, 120)}</p>\n")
        out.write("</body></html>\n")


def make_html_article(path: Path, size: int, rng: random.Random) -> None:
    """A news page for the article mode (004): menu, cookie banner, aside and footer around an
    article with every construct of the subset (headings, emphasis, links, lists, quotes, tables,
    code, images)."""
    with path.open("w", encoding="utf-8") as out:
        out.write(
            "<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'><title>bench</title></head>"
            "<body><nav><a href='/'>Inicio</a> <a href='/x'>Sección</a></nav>"
            "<div class='cookies'>Usamos cookies. <button>Aceptar</button></div>"
            f"<main><article><h1>{_words(rng, 6)}</h1>"
        )
        number = 0
        while out.tell() < size:
            number += 1
            out.write(
                f"<h2>{_words(rng, 3)}</h2><p>{_words(rng, 40)} <strong>{_words(rng, 2)}</strong>"
                f" {_words(rng, 30)} <em>{_words(rng, 2)}</em> <a href='https://example.org/{number}'>"
                f"{_words(rng, 3)}</a> {_words(rng, 40)}</p>"
                f"<ul><li>{_words(rng, 5)}</li><li>{_words(rng, 5)}<ul><li>{_words(rng, 4)}</li>"
                f"</ul></li></ul><blockquote><p>{_words(rng, 20)}</p></blockquote>"
                f"<table><tr><th>{_words(rng, 1)}</th><th>{_words(rng, 1)}</th></tr>"
                f"<tr><td>{number}</td><td>{_words(rng, 2)}</td></tr></table>"
                f"<pre><code>x = {number}</code></pre>"
                f"<figure><img src='https://cdn.example/{number}.jpg'"
                f" alt='{_words(rng, 3)}'></figure>"
                f"<p>{_words(rng, 60)}</p>\n"
            )
        out.write(
            "</article><aside>Te puede interesar</aside></main>"
            "<footer>© 2026</footer></body></html>\n"
        )


def make_ipynb(path: Path, size: int, rng: random.Random) -> None:
    cells: list[dict[str, Any]] = []
    written = 0
    while written < size:
        text = _words(rng, 150)
        cells.append({"cell_type": "markdown", "metadata": {}, "source": [text]})
        cells.append(
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [f"value = {rng.random()!r}\n", "print(value)"],
            }
        )
        written += len(text) + 120
    notebook = {"cells": cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    path.write_text(json.dumps(notebook), encoding="utf-8")
