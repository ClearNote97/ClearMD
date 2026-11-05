r"""The parsing context: pylatexenc's defaults plus what ClearMD needs to read real documents.

pylatexenc does not know the arguments of many common commands (``\href``, ``\caption``,
``\paragraph``, ``\index``…), parses ``lstlisting`` and ``minted`` as ordinary LaTeX (a ``$`` in
code would become math), reads ``\url`` as LaTeX (a ``%`` would start a comment) and has no
``\def``. They are declared here; a parse error never stops the parse (tolerant mode), and the
first one is kept for the ``parse_recovered`` note.
"""

from clearmd.backend.services.conversion.tex.parsing.braces import forget_brace_pairs
from clearmd.backend.services.conversion.tex.parsing.mask import mask
from clearmd.backend.services.conversion.tex.parsing.specs import (
    CITATION_MACROS,
    CODE_ENVIRONMENTS,
    REFERENCE_MACROS,
    make_context,
)
from clearmd.backend.services.conversion.tex.parsing.walker import Unparseable, parse

__all__ = [
    "CITATION_MACROS",
    "CODE_ENVIRONMENTS",
    "REFERENCE_MACROS",
    "Unparseable",
    "forget_brace_pairs",
    "make_context",
    "mask",
    "parse",
]
