"""What is not LaTeX to look into for includes, replaced by spaces."""

import re

from clearmd.backend.services.conversion.tex.parsing.braces import balanced_end
from clearmd.backend.services.conversion.tex.parsing.cursor import VERB_WINDOW

# What is not LaTeX to look into for includes: comments (a "%" after an even run of backslashes),
# code environments, the comment environment, \verb and \lstinline, \iffalse … \fi (nested
# conditionals counted) and URL arguments.
_NOT_SOURCE = re.compile(
    r"(?<!\\)(?:\\\\)*%"
    r"|\\begin\s*\{(verbatim\*?|Verbatim\*?|BVerbatim|LVerbatim|lstlisting|minted|comment)\}"
    r"|\\(?:verb\*?|lstinline(?:\[[^\]\n]{0,256}\])?)([^\sA-Za-z*])"
    r"|\\iffalse(?![A-Za-z@])"
    r"|\\(?:url|href)\s*(?=\{)"
)


# \ifthenelse is a macro of the ifthen package, not a TeX conditional: it has no \fi.
_CONDITIONAL = re.compile(r"\\(if(?!thenelse)[A-Za-z@]*|fi)(?![A-Za-z@])")


def matching_fi(text: str, start: int) -> int | None:
    r"""The end of the ``\fi`` closing a conditional opened just before ``start`` (nested ones
    counted), or ``None``."""
    depth = 1
    for found in _CONDITIONAL.finditer(text, start):
        depth += -1 if found.group(1) == "fi" else 1
        if depth == 0:
            return found.end()
    return None


def mask(text: str) -> str:
    """``text`` with what is not source replaced by spaces (same length, newlines kept)."""
    pieces, cursor = [], 0
    while (found := _NOT_SOURCE.search(text, cursor)) is not None:
        start, token = found.start(), found.group(0)
        if token.endswith("%"):
            start = found.end() - 1
            line_end = text.find("\n", start)
            end = len(text) if line_end == -1 else line_end
        elif found.group(1):
            close = text.find(f"\\end{{{found.group(1)}}}", found.end())
            end = len(text) if close == -1 else close
        elif found.group(2):
            delimiter = "}" if found.group(2) == "{" else found.group(2)
            limit = min(len(text), found.end() + VERB_WINDOW)
            line_end = text.find("\n", found.end(), limit)
            close = text.find(delimiter, found.end(), limit if line_end == -1 else line_end)
            end = found.end() if close == -1 else close + 1
        elif token.startswith("\\iffalse"):
            fi = matching_fi(text, found.end())
            end = found.end() if fi is None else fi  # unclosed: not a comment (noted when read)
        else:  # \url{…} or \href{…}: read as written by UrlArgsParser
            close = balanced_end(text, found.end(), comments=False)
            end = found.end() if close == -1 else close + 1
        pieces.append(text[cursor:start])
        pieces.append(re.sub(r"[^\n]", " ", text[start:end]))
        cursor = max(end, found.end())
    pieces.append(text[cursor:])
    return "".join(pieces)
