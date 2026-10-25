r"""LaTeX nodes → Markdown: the supported subset of spec 002, everything else kept and reported.

Text-mode nodes follow the subset table; math is re-serialized untouched; a command that neither
this renderer nor pylatexenc's ``latex2text`` knows is written back as is and listed in a note.
"""

import re
from collections.abc import Callable
from typing import Any

from pylatexenc.latex2text import LatexNodes2Text, get_default_latex_context_db
from pylatexenc.latexwalker import (
    LatexCharsNode,
    LatexCommentNode,
    LatexEnvironmentNode,
    LatexGroupNode,
    LatexMacroNode,
    LatexMathNode,
    LatexSpecialsNode,
)

from clearmd.backend.schemas.models import ConversionResult
from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind
from clearmd.backend.services.conversion.tex.context import (
    CITATION_MACROS,
    REFERENCE_MACROS,
    make_context,
    parse,
)
from clearmd.backend.services.conversion.tex.macros import (
    BudgetExceeded,
    MacroExpander,
    collect_definitions,
)
from clearmd.backend.services.conversion.tex.tables import tabular_to_markdown

SECTION_LEVELS = {
    "part": 0,
    "chapter": 1,
    "section": 2,
    "subsection": 3,
    "subsubsection": 4,
    "paragraph": 5,
    "subparagraph": 6,
}
_CONTROL_WORD_AT_END = re.compile(r"\\[A-Za-z]+$")
_SECTIONING = re.compile(r"\\(" + "|".join(SECTION_LEVELS) + r")\*?\s*[\[{]")
_BABEL = re.compile(r"\\usepackage\s*\[([^\]]*)\]\s*\{babel\}|\\setmainlanguage\s*\{([^}]*)\}")

INLINE = {
    "textbf": "**{}**",
    "textit": "*{}*",
    "textsl": "*{}*",
    "emph": "*{}*",
    "texttt": "`{}`",
    "underline": "<u>{}</u>",
}
PLAIN = frozenset(
    {"textrm", "textsf", "textsc", "textup", "textmd", "textnormal", "mbox", "hbox", "text"}
)
# Layout, metadata and definitions: nothing to show (definitions are expanded by macros.py).
DROPPED = frozenset(
    {
        "label", "index", "vspace", "hspace", "newpage", "clearpage", "cleardoublepage",
        "noindent", "centering", "tableofcontents", "listoffigures", "listoftables", "medskip",
        "bigskip", "smallskip", "vfill", "hfill", "linebreak", "pagebreak", "nopagebreak",
        "raggedright", "raggedleft", "documentclass", "usepackage", "graphicspath",
        "bibliographystyle", "bibliography", "printbibliography", "addbibresource", "pagestyle",
        "thispagestyle", "setlength", "setcounter", "addcontentsline", "phantomsection",
        "frontmatter", "mainmatter", "backmatter", "appendix", "title", "author", "date",
        "thanks", "newcommand", "renewcommand", "providecommand", "DeclareMathOperator", "def",
        "makeatletter", "makeatother", "small", "footnotesize", "large", "Large", "LARGE",
        "normalsize", "tiny", "huge", "Huge", "scriptsize", "bfseries", "itshape", "rmfamily",
        "sffamily", "ttfamily", "selectlanguage", "onehalfspacing", "doublespacing",
        "singlespacing", "nocite", "hline", "toprule", "midrule", "bottomrule", "today",
    }
)  # fmt: skip
WORDS = {"LaTeX": "LaTeX", "TeX": "TeX", "LaTeXe": "LaTeX2e"}
SPECIALS = {"~": "\u00a0", "--": "–", "---": "—", "``": "“", "''": "”", "!`": "¡", "?`": "¿"}
INCLUDES = frozenset({"input", "include", "subfile"})

LISTS = frozenset({"itemize", "enumerate", "description"})
QUOTES = frozenset({"quote", "quotation", "verse"})
CODE = frozenset({"verbatim", "verbatim*", "lstlisting", "minted"})
DISPLAY_MATH = frozenset({"equation", "equation*", "displaymath", "math"})
ALIGNED = {
    "align": "aligned",
    "align*": "aligned",
    "flalign": "aligned",
    "flalign*": "aligned",
    "eqnarray": "aligned",
    "eqnarray*": "aligned",
    "multline": "aligned",
    "multline*": "aligned",
    "gather": "gathered",
    "gather*": "gathered",
}
CONTAINERS = frozenset({"center", "flushleft", "flushright", "minipage", "document"})
FIGURES = frozenset({"figure", "figure*", "wrapfigure"})
TABLES = frozenset({"table", "table*"})
TABULARS = frozenset({"tabular", "tabular*", "tabularx", "longtable"})

_LATEX2TEXT = LatexNodes2Text(math_mode="verbatim", strict_latex_spaces=False)
_LATEX2TEXT_DB = get_default_latex_context_db()

# Resolves an include argument to the rendered Markdown of that file, or ``None`` if not followed.
IncludeHandler = Callable[[str], str | None]
ImageHandler = Callable[[str], str]


def _block(text: str) -> str:
    return f"\n\n{text.strip(chr(10))}\n\n"


def _raw(node: Any) -> str:
    """The LaTeX source of an argument without its outer braces."""
    if node is None:
        return ""
    if isinstance(node, LatexGroupNode):
        return "".join(child.latex_verbatim() for child in node.nodelist or [])
    text: str = node.latex_verbatim()
    return text


def _fence(code: str) -> str:
    longest = max((len(run) for run in re.findall("`+", code)), default=0)
    return "`" * max(3, longest + 1)


def _indent(text: str, width: int) -> str:
    lines = text.split("\n")
    return "\n".join([lines[0], *[(" " * width + line) if line else "" for line in lines[1:]]])


class Renderer:
    def __init__(
        self,
        source: str,
        *,
        include: IncludeHandler | None = None,
        image: ImageHandler | None = None,
        macros: MacroExpander | None = None,
    ) -> None:
        self._include = include
        self._image = image or (lambda path: path)
        self._macros = macros
        present = [SECTION_LEVELS[name] for name in _SECTIONING.findall(source)]
        self._top_level = min(present, default=SECTION_LEVELS["section"])
        babel = _BABEL.search(source)
        languages = ",".join(group or "" for group in babel.groups()) if babel else ""
        self._spanish = "spanish" in languages or "español" in languages
        self.unknown: dict[str, None] = {}
        self.tables_kept = 0
        self.footnotes: list[str] = []
        self.metadata: dict[str, list[Any]] = {}

    # --- Entry points -------------------------------------------------------------------------

    def document(self, nodes: list[Any]) -> str:
        body = nodes
        for node in nodes:
            if isinstance(node, LatexEnvironmentNode) and node.environmentname == "document":
                self._collect_metadata(nodes[: nodes.index(node)])
                body = node.nodelist or []
                break
        else:
            self._collect_metadata(nodes)
        text = self.render(body)
        if self.footnotes:
            notes = "\n".join(f"[^{n}]: {note}" for n, note in enumerate(self.footnotes, start=1))
            text += _block(notes)
        return _tidy(text)

    def render(self, nodes: list[Any]) -> str:
        parts = []
        after_unknown = False
        skip = 0
        for node in nodes:
            if node is None:
                continue
            if skip:  # the name and body of a \def
                skip -= 1
                if isinstance(node, LatexMacroNode) or isinstance(node, LatexGroupNode):
                    continue
                skip = 0
            if _is_macro(node, "def"):
                skip = 2
                continue
            if after_unknown and isinstance(node, LatexGroupNode):
                parts.append(node.latex_verbatim())  # its arguments, as written
                continue
            before = len(self.unknown)
            parts.append(self._node(node))
            after_unknown = isinstance(node, LatexMacroNode) and len(self.unknown) > before
        return "".join(parts)

    def inline(self, nodes: list[Any]) -> str:
        return re.sub(r"\s+,", ",", " ".join(self.render(nodes).split()))

    # --- Nodes ------------------------------------------------------------------------------

    def _node(self, node: Any) -> str:
        if isinstance(node, LatexCharsNode):
            text: str = node.chars
            return text
        if isinstance(node, LatexCommentNode):
            return ""
        if isinstance(node, LatexSpecialsNode):
            chars = str(node.specials_chars)
            return SPECIALS.get(chars, chars)
        if isinstance(node, LatexGroupNode):
            return self.render(node.nodelist or [])
        if isinstance(node, LatexMathNode):
            return self._math(node)
        if isinstance(node, LatexMacroNode):
            return self._macro(node)
        if isinstance(node, LatexEnvironmentNode):
            return self._environment(node)
        return ""

    def _arg(self, node: Any, index: int) -> Any:
        arguments = getattr(getattr(node, "nodeargd", None), "argnlist", None) or []
        return arguments[index] if index < len(arguments) else None

    def _arg_nodes(self, node: Any, index: int) -> list[Any]:
        argument = self._arg(node, index)
        if argument is None:
            return []
        if isinstance(argument, LatexGroupNode):
            return list(argument.nodelist or [])
        return [argument]

    def _last_arg(self, node: Any) -> list[Any]:
        arguments = getattr(getattr(node, "nodeargd", None), "argnlist", None) or []
        return self._arg_nodes(node, len(arguments) - 1) if arguments else []

    def _macro(self, node: Any) -> str:
        name: str = node.macroname
        if self._macros is not None and self._macros.knows(name):
            return self._expanded(node, self.render)
        if name in SECTION_LEVELS:
            level = 2 + max(0, SECTION_LEVELS[name] - self._top_level)
            return _block("#" * min(6, level) + " " + self.inline(self._last_arg(node)))
        if name in INLINE:
            return INLINE[name].format(self.inline(self._last_arg(node)))
        if name in PLAIN:
            return self.render(self._last_arg(node))
        if name == "maketitle":
            return self._title_block()
        if name == "href":
            return f"[{self.inline(self._arg_nodes(node, 1))}]({_raw(self._arg(node, 0)).strip()})"
        if name == "url":
            return f"<{_raw(self._arg(node, 0)).strip()}>"
        if name == "verb":
            code = node.nodeargd.verbatim_text
            return f"`{code}`" if "`" not in code else f"`` {code} ``"
        if name == "footnote":
            self.footnotes.append(self.inline(self._last_arg(node)))
            return f"[^{len(self.footnotes)}]"
        if name in CITATION_MACROS:
            keys = [key.strip() for key in _raw(self._arg(node, 3)).split(",") if key.strip()]
            note = _raw(self._arg(node, 2)) or _raw(self._arg(node, 1))
            cited = "; ".join(f"@{key}" for key in keys)
            return f"[{cited}, {note.strip()}]" if note.strip() else f"[{cited}]"
        if name in REFERENCE_MACROS:
            return f"({_raw(self._arg(node, 0)).strip()})"
        if name in INCLUDES:
            return self._include_file(node)
        if name == "\\":
            return "  \n"
        if name == "par":
            return "\n\n"
        if name == "and":
            return ", "
        if name in DROPPED:
            return ""
        if name in WORDS:
            return WORDS[name]
        if _LATEX2TEXT_DB.get_macro_spec(name) is not None:
            return str(_LATEX2TEXT.nodelist_to_text([node]))
        return self._unknown(f"\\{name}", node)

    def _environment(self, node: Any) -> str:
        name: str = node.environmentname
        if name in CONTAINERS:
            return self.render(node.nodelist or [])
        if name == "abstract":
            heading = "Resumen" if self._spanish else "Abstract"
            return _block(f"## {heading}") + _block(self.render(node.nodelist or []))
        if name in LISTS:
            return _block(self._list(node))
        if name in QUOTES:
            body = self.render(node.nodelist or []).strip()
            return _block("\n".join(f"> {line}" if line else ">" for line in body.split("\n")))
        if name in CODE:
            return _block(self._code(node))
        if name in DISPLAY_MATH:
            return _block(f"$$\n{self._math_body(node.nodelist)}\n$$")
        if name in ALIGNED:
            inner = ALIGNED[name]
            body = self._math_body(node.nodelist)
            return _block(f"$$\n\\begin{{{inner}}}\n{body}\n\\end{{{inner}}}\n$$")
        if name in FIGURES:
            return self._figure(node)
        if name in TABLES:
            return self._table_float(node)
        if name in TABULARS:
            return self._tabular(node)
        return self._unknown(f"\\begin{{{name}}}", node)

    def _unknown(self, label: str, node: Any) -> str:
        self.unknown[label] = None
        text: str = node.latex_verbatim()
        return text

    # --- Pieces -------------------------------------------------------------------------------

    def _collect_metadata(self, preamble: list[Any]) -> None:
        for node in preamble:
            if isinstance(node, LatexMacroNode) and node.macroname in {"title", "author", "date"}:
                self.metadata[node.macroname] = self._last_arg(node)

    def _title_block(self) -> str:
        title = self.inline(self.metadata.get("title", []))
        if not title:
            return ""
        byline = " · ".join(
            part
            for part in (self.inline(self.metadata.get(k, [])) for k in ("author", "date"))
            if part
        )
        return _block(f"# {title}" + (f"\n\n*{byline}*" if byline else ""))

    def _math(self, node: Any) -> str:
        body = self._math_body(node.nodelist)
        if node.displaytype == "display":
            return _block(f"$$\n{body}\n$$")
        return f"${body}$"

    def _math_body(self, nodes: list[Any] | None) -> str:
        return " ".join(self._math_source(list(nodes or [])).split())

    # --- The author's macros ------------------------------------------------------------------

    def _expanded(self, node: Any, serialize: Callable[[list[Any]], str]) -> str:
        """A use of an author's macro, expanded; past the budget the top-level use stays as is."""
        assert self._macros is not None
        top = self._macros.depth == 0
        try:
            with self._macros.nested():
                return serialize(self._macros.expand(node))
        except BudgetExceeded:
            if not top:
                raise
            if self._macros.limited is None:
                self._macros.limited = f"\\{node.macroname}"
            text: str = node.latex_verbatim()
            return text

    def _math_source(self, nodes: list[Any]) -> str:
        return "".join(self._serialize(n) for n in nodes if n is not None and not _is_label(n))

    def _serialize(self, node: Any) -> str:
        """Math as written, with only the spans that use an author's macro replaced."""
        verbatim: str = node.latex_verbatim()
        if self._macros is None:
            return verbatim
        if isinstance(node, LatexMacroNode) and self._macros.knows(node.macroname):
            text = self._expanded(node, self._math_source)
            # "\\R x" must not become "\\mathbb{R}x" glued to a following letter by mistake.
            if text != verbatim and _CONTROL_WORD_AT_END.search(text):
                text += " "
            return text
        children = sorted((c for c in _children(node) if c is not None), key=lambda c: c.pos)
        if not any(self._uses_author_macro(child) for child in children):
            return verbatim
        source: str = node.parsing_state.s
        parts, cursor = [], node.pos
        for child in children:
            parts.append(source[cursor : child.pos])
            parts.append(self._serialize(child))
            cursor = child.pos + child.len
        parts.append(source[cursor : node.pos + node.len])
        return "".join(parts)

    def _uses_author_macro(self, node: Any) -> bool:
        assert self._macros is not None
        if isinstance(node, LatexMacroNode) and self._macros.knows(node.macroname):
            return True
        return any(self._uses_author_macro(c) for c in _children(node) if c is not None)

    def _list(self, node: Any) -> str:
        items: list[tuple[Any, list[Any]]] = []
        for child in node.nodelist or []:
            if isinstance(child, LatexMacroNode) and child.macroname == "item":
                items.append((child, []))
            elif items:
                items[-1][1].append(child)
        lines = []
        for number, (item, content) in enumerate(items, start=1):
            if node.environmentname == "enumerate":
                marker = f"{number}. "
            else:
                marker = "- "
            text = self.render(content).strip()
            if node.environmentname == "description":
                term = self.inline(self._arg_nodes(item, 0))
                text = f"**{term}** {text}" if term else text
            text = re.sub(r"\n[ \t]*\n+", "\n", text)  # tight items, nested lists included
            lines.append(marker + _indent(text, len(marker)))
        return "\n".join(lines)

    def _code(self, node: Any) -> str:
        raw: str = node.nodeargd.verbatim_text if node.nodeargd is not None else ""
        language = ""
        if node.environmentname == "lstlisting":
            options = re.match(r"\s*\[([^\]]*)\]", raw)
            if options:
                raw = raw[options.end() :]
                found = re.search(r"language\s*=\s*\{?([\w+#-]+)", options.group(1))
                language = found.group(1).lower() if found else ""
        elif node.environmentname == "minted":
            declared = re.match(r"\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}", raw)
            if declared:
                raw = raw[declared.end() :]
                language = declared.group(1).strip().lower()
        code = raw.strip("\n")
        fence = _fence(code)
        return f"{fence}{language}\n{code}\n{fence}"

    def _figure(self, node: Any) -> str:
        images = [n for n in _walk(node.nodelist) if _is_macro(n, "includegraphics")]
        captions = [n for n in _walk(node.nodelist) if _is_macro(n, "caption")]
        caption = self.inline(self._last_arg(captions[0])) if captions else ""
        if not images:
            return _block(f"*{caption}*") if caption else ""
        shown = []
        for image in images:
            target = self._image(_raw(self._last_arg_node(image)).strip())
            shown.append(f"![{caption}]({target})")
        return _block("\n\n".join(shown))

    def _last_arg_node(self, node: Any) -> Any:
        arguments = getattr(getattr(node, "nodeargd", None), "argnlist", None) or []
        return arguments[-1] if arguments else None

    def _table_float(self, node: Any) -> str:
        parts = []
        caption = ""
        for child in node.nodelist or []:
            if _is_macro(child, "caption"):
                caption = self.inline(self._last_arg(child))
            elif not _is_macro(child, "centering"):
                parts.append(self._node(child))
        text = "".join(parts)
        return text + (_block(f"*{caption}*") if caption else "")

    def _tabular(self, node: Any) -> str:
        table = tabular_to_markdown(node, self.inline)
        if table is None:
            self.tables_kept += 1
            return _block(f"```latex\n{node.latex_verbatim()}\n```")
        return _block(table)

    def _include_file(self, node: Any) -> str:
        argument = _raw(self._arg(node, 0)).strip()
        rendered = self._include(argument) if self._include else None
        if rendered is None:
            return f"`{node.latex_verbatim().strip()}`"
        return rendered

    def notes(self) -> tuple[ConversionNote, ...]:
        found: list[ConversionNote] = []
        if self.unknown:
            items = tuple(NoteItem(name) for name in self.unknown)
            found.append(ConversionNote(NoteKind.UNKNOWN_COMMANDS, items))
        if self._macros is not None and self._macros.exhausted is not None:
            limit = NoteItem(self._macros.limited or "", self._macros.exhausted.value)
            found.append(ConversionNote(NoteKind.MACRO_LIMIT_REACHED, (limit,)))
        if self.tables_kept:
            found.append(
                ConversionNote(NoteKind.TABLE_KEPT_AS_LATEX, (NoteItem(str(self.tables_kept)),))
            )
        return tuple(found)


def _is_macro(node: Any, name: str) -> bool:
    return isinstance(node, LatexMacroNode) and node.macroname == name


def _is_label(node: Any) -> bool:
    return _is_macro(node, "label")


def _children(node: Any) -> list[Any]:
    arguments = getattr(getattr(node, "nodeargd", None), "argnlist", None) or []
    return [*(getattr(node, "nodelist", None) or []), *arguments]


def _walk(nodes: list[Any] | None) -> list[Any]:
    found = []
    for node in nodes or []:
        if node is None:
            continue
        found.append(node)
        found.extend(_walk(getattr(node, "nodelist", None)))
    return found


def _tidy(text: str) -> str:
    # Trailing spaces go, except a hard line break ("  ") after real text.
    lines = [
        line if line.endswith("  ") and line.strip() else line.rstrip() for line in text.split("\n")
    ]
    joined = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", joined).strip() + "\n"


def author_macros(nodes: list[Any], source_size: int) -> MacroExpander | None:
    """The expander for the definitions in ``nodes``, or ``None`` when there are none."""
    definitions = collect_definitions(nodes)
    return MacroExpander(definitions, source_size) if definitions else None


def render_latex(text: str) -> ConversionResult:
    """Convert one LaTeX source (no includes followed: see ``TexConverter``)."""
    nodes, error = parse(text, make_context())
    macros = author_macros(nodes, len(text))
    if macros is not None:
        nodes, error = parse(text, macros.context)
    renderer = Renderer(text, macros=macros)
    markdown = renderer.document(nodes)
    notes = list(renderer.notes())
    if error:
        notes.append(ConversionNote(NoteKind.PARSE_RECOVERED, (NoteItem(error),)))
    return ConversionResult(markdown, tuple(notes))
