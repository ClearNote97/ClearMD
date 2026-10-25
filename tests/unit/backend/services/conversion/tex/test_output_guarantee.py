"""The output guarantee of ADR-0023, checked with a real CommonMark parser.

For hostile LaTeX, the Markdown ClearMD writes must hold no raw HTML, no image, no link but the
ones ClearMD decided, and no block structure written by the document. Every finding of the three
verification rounds is in the corpus, plus every combination of a dangerous prefix, a ClearMD
construct and a dangerous suffix.
"""

import itertools
import re
from collections.abc import Iterator
from typing import Any

import pytest
from markdown_it import MarkdownIt

from clearmd.backend.services.conversion.tex.render import render_latex

OK_LINK = "https://ok.example/page"
PARSER = MarkdownIt("commonmark", {"html": True}).enable("table")
# Blocks a paragraph of hostile text may legitimately produce: ClearMD's own code.
ALLOWED_BLOCKS = {"paragraph_open", "paragraph_close", "inline", "fence"}

HOSTILE = [
    # inline HTML and links through every path
    "<img src=x> y",
    "\\ref{a] [t](javascript:alert(1)) [b}",
    "\\cite{<img src=x>}",
    "\\begin{zz}<img src=x> ![](http://evil.example/c.png)\\end{zz}",
    "\\unknownmacro{<img src=x>}{![](http://evil.example/c.png)}",
    "$a <img src=x> b$",
    "\\textless img src=x\\textgreater",
    "\\char60 img src=x>",
    'x \\char"E000 # y',
    "a ` \\verb|<img src=x>|",
    "a ` \\texttt{![x](http://evil.example/b.png)}",
    "a ` $x$ `<img src=x>`",
    "$\\texttt{![x](http://evil.example/b.png)}$",
    "$`$ \\verb|<img src=x>| $`$",
    "\\texttt{\\footnote{<img src=x>}}",
    "!\\cite{a}(http://evil.example/b.png)",
    "!\\cite{a}\\ref{http://evil.example/b.png}",
    "!\\footnote{x}(http://evil.example/b.png)",
    "\\cite{b}(javascript:alert(1))",
    f"!\\href{{{OK_LINK}}}{{x}}",  # the author's link stays a link, never an image
    "\\href{//evil.example/b.png}{x}",
    "\\href{javascript&#58;alert(1)}{click}",
    "\\includegraphics{https&#58;//evil.example/a.png}",
    "\\includegraphics{//evil.example/a.png}",
    # block structure written by the document
    "Antes.\n\n\\# titulo",
    "Antes.\n\n1{}. item",
    "Antes.\n\n-{} item",
    "Titulo\n===\n",
    "Titulo\n-\n",
    "Titulo\n-{}-\n",
    "Antes.\n\n***\n",
    "Antes.\n\n\\textasciitilde\\textasciitilde\\textasciitilde\nDespues.",
    "Antes.\n\n\\cite{a}: http://evil.example/b.png\n\n\\cite{a} !\\cite{a}",
    "text\r# h\r- i\r> q",
    "text\r\n# h\r\n- i",
    "\\[ # x \\]",
    "\\[ - x \\]",
    "\\[ > x \\]",
    "\\[ --- \\]",
    "\\[ = \\]",
    "a | b\n|---|---|\n c | d",
    "Antes.\n\n        indented code\n",
    "Antes.\n\n\t\tindented with tabs\n",
    "Antes.\n\n{\t\\url{x}} tab",
    "\\url{texto    } y \\url{a b}",
    "\\url{texto_\n\n#~\r<\\texttt{![x](http://evil.example/b.png)}#}",
    "\\url{t\n\n\\verb|<img src=x>|}",
    "\\verb|<img src=x>|\\url{a `b}\\texttt{![x](http://evil.example/b.png)}",
]

PREFIXES = ["!", "`", "a `", "]", "\\#", ""]
CONSTRUCTS = [
    "\\cite{a}",
    "\\footnote{x}",
    "\\ref{r}",
    f"\\href{{{OK_LINK}}}{{x}}",
    "\\texttt{![x](http://evil.example/b.png)}",
    "\\verb|<img src=x>|",
    "$x$",
]
SUFFIXES = ["(http://evil.example/b.png)", ": http://evil.example/b.png", "`", "[x]", ""]
COMBINATIONS = [
    f"{prefix}{construct}{suffix}"
    for prefix, construct, suffix in itertools.product(PREFIXES, CONSTRUCTS, SUFFIXES)
]


def _doc(body: str) -> str:
    return f"\\documentclass{{article}}\\begin{{document}}{body}\\end{{document}}"


def _tokens(markdown: str) -> Iterator[Any]:
    for token in PARSER.parse(markdown):
        yield token
        yield from token.children or []


def _blocks(markdown: str) -> Iterator[Any]:
    return iter(PARSER.parse(markdown))


_FOOTNOTE_DEFINITION = re.compile(r"(?m)^\[\^\d+\]: .*$")


def _broken_promises(latex: str) -> list[str]:
    markdown = render_latex(_doc(latex)).markdown
    found = []
    if re.search(r"(?<!\\)!\[\^\d+\]", markdown):
        found.append("image: a footnote reference after '!'")
    # A viewer with footnotes (GitHub, Obsidian) reads ClearMD's definitions as footnotes, not as
    # link references; plain CommonMark has no footnotes, so they are taken out before parsing.
    markdown = _FOOTNOTE_DEFINITION.sub("", markdown)
    for token in _tokens(markdown):
        if token.type in {"html_inline", "html_block"}:
            found.append(f"html: {token.content!r}")
        elif token.type == "image":
            found.append(f"image: {token.attrs.get('src')!r}")
        elif token.type == "link_open" and token.attrs.get("href") != OK_LINK:
            found.append(f"link: {token.attrs.get('href')!r}")
    for token in _blocks(markdown):
        if token.nesting >= 0 and token.level == 0 and token.type not in ALLOWED_BLOCKS:
            found.append(f"block: {token.type}")
    return [f"{problem} in {markdown!r}" for problem in found]


@pytest.mark.parametrize("latex", HOSTILE)
def test_hostile_text_never_breaks_the_guarantee(latex: str) -> None:
    assert _broken_promises(latex) == []


def test_no_combination_of_dangerous_neighbours_breaks_it() -> None:
    broken = {latex: problems for latex in COMBINATIONS if (problems := _broken_promises(latex))}
    assert broken == {}


def test_clearmds_own_structure_survives_the_parser() -> None:
    markdown = render_latex(
        _doc(
            "\\section{S}\\begin{itemize}\\item a\\begin{enumerate}\\item b\\end{enumerate}"
            "\\end{itemize}\\begin{quote}q\\end{quote}\\begin{tabular}{cc}x & y\\\\\\end{tabular}"
            f"\\href{{{OK_LINK}}}{{link}} \\texttt{{a[0] < b}} $a < b$ \\underline{{u}}"
        )
    ).markdown
    types = [token.type for token in _tokens(markdown)]
    for expected in (
        "heading_open",
        "bullet_list_open",
        "ordered_list_open",
        "blockquote_open",
        "table_open",
        "link_open",
        "code_inline",
    ):
        assert expected in types, expected
    assert "a[0] < b" in markdown and "$a < b$" in markdown and "<u>u</u>" in markdown


# Pieces only: ClearMD's own block structure (lists, quotes) is tested on its own above.
ALPHABET = [
    *PREFIXES,
    *CONSTRUCTS,
    *SUFFIXES,
    "texto",
    " ",
    "\n",
    "\n\n",
    "\r",
    "\t",
    "    ",
    "<",
    ">",
    "&#58;",
    "&lt;",
    "#",
    "-",
    "=",
    "*",
    "_",
    "|",
    "~",
    "1.",
    "{",
    "}",
    "{}",
    "\\\\",
    "\\#",
    "\\&",
    "%",
    "$",
    "\\[ x \\]",
    "\\emph{",
    "\\textbf{e}",
    "\\iffalse",
    "\\fi",
    "\\url{",
    f"\\url{{{OK_LINK}}}",
    "\\includegraphics{http://evil.example/i.png}",
    "\\textless",
    "\\textasciitilde",
    "\\char96",
    '\\char"E000',
    "\\newcommand{\\m}{![a](http://evil.example/m.png)}\\m",
]


def test_a_seeded_fuzz_of_dangerous_pieces_never_breaks_it() -> None:
    import random

    rng = random.Random(2026)
    broken = {}
    for _ in range(1500):
        latex = "".join(rng.choice(ALPHABET) for _ in range(rng.randint(2, 14)))
        if problems := _broken_promises(latex):
            broken[latex] = problems
    assert dict(itertools.islice(broken.items(), 5)) == {}
