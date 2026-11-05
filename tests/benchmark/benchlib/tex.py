"""The LaTeX generators (feature 002)."""

import random
from pathlib import Path

from benchlib.common import _line, _words

_TEX_PREAMBLE = (
    "\\documentclass{article}\n\\usepackage[spanish]{babel}\n"
    "\\title{Benchmark}\\author{ClearMD}\\date{2026}\n\\begin{document}\n\\maketitle\n"
)
_TEX_MACROS = (
    "\\newcommand{\\R}{\\mathbb{R}}\n"
    "\\newcommand{\\norm}[1]{\\left\\lVert #1 \\right\\rVert}\n"
    "\\newcommand{\\pair}[2][0]{(#1, #2)}\n"
    "\\newcommand{\\term}[1]{\\textbf{#1}}\n"
    "\\newcommand{\\vecx}{\\mathbf{x}}\n"
    "\\DeclareMathOperator{\\argmax}{arg\\,max}\n"
    "\\def\\tool{ClearMD}\n"
)


def _tex_paragraph(rng: random.Random, macros: bool) -> str:
    words = _words(rng, rng.randint(40, 70)).split()
    for _ in range(4):
        at = rng.randrange(len(words))
        words[at] = rng.choice(
            [
                f"\\textbf{{{words[at]}}}",
                f"\\emph{{{words[at]}}}",
                f"\\texttt{{{words[at]}}}",
                f"\\cite{{{words[at]}{rng.randint(1, 99)}}}",
                f"$x_{{{rng.randint(1, 9)}}}^2 + y$",
                "Nicol\\'as --- ``cita''",
            ]
        )
    if macros:
        for _ in range(4):
            at = rng.randrange(len(words))
            words[at] = rng.choice(
                [
                    "$\\vecx \\in \\R^n$",
                    f"$\\norm{{\\vecx_{rng.randint(1, 9)}}}$",
                    f"$\\pair[{rng.randint(1, 9)}]{{b}}$",
                    f"\\term{{{words[at]}}}",
                    "$\\argmax_{\\theta} f$",
                    "\\tool{}",
                ]
            )
    text = " ".join(words) + "."
    if rng.random() < 0.3:
        text += f"\\footnote{{{_words(rng, 8)}.}}"
    return text


def _tex_block(rng: random.Random, number: int) -> str:
    choice = number % 4
    if choice == 0:
        items = "".join(f"\\item {_line(rng)}\n" for _ in range(3))
        return f"\\begin{{itemize}}\n{items}\\end{{itemize}}"
    if choice == 1:
        body = f"\\label{{eq:{number}}}\na_{number}^2 + b^2 = c^2"
        return f"\\begin{{equation}}{body}\n\\end{{equation}}"
    if choice == 2:
        rows = "".join(f"{_words(rng, 1)} & {rng.randint(1, 999)} \\\\\n" for _ in range(4))
        return (
            "\\begin{table}\\centering\n\\begin{tabular}{lr}\n\\hline\n"
            f"{rows}\\hline\n\\end{{tabular}}\n\\caption{{{_words(rng, 3)}}}\n\\end{{table}}"
        )
    return f"\\begin{{quote}}{_line(rng)}\\end{{quote}}"


def _tex(path: Path, size: int, rng: random.Random, *, macros: bool) -> None:
    with path.open("w", encoding="utf-8") as out:
        out.write(_TEX_MACROS if macros else "")
        out.write(_TEX_PREAMBLE)
        number = 0
        while out.tell() < size:
            number += 1
            out.write(f"\\section{{{_words(rng, 3)}}}\n")
            for _ in range(3):
                out.write(_tex_paragraph(rng, macros) + "\n\n")
            out.write(_tex_block(rng, number) + "\n\n")
        out.write("\\end{document}\n")


def make_tex(path: Path, size: int, rng: random.Random) -> None:
    _tex(path, size, rng, macros=False)


def make_tex_macros(path: Path, size: int, rng: random.Random) -> None:
    _tex(path, size, rng, macros=True)
