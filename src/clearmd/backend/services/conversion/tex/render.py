r"""LaTeX nodes → Markdown: the supported subset of spec 002, everything else kept and reported.

Text-mode nodes follow the subset table; math is re-serialized as written (comments dropped, the
author's macros expanded); a command that neither this renderer nor pylatexenc's ``latex2text``
knows is written back as is and listed in a note. A source pylatexenc cannot read at all (deep
nesting) is kept whole as a LaTeX code block, with a note: a file never fails as a whole (AC-21).
"""

import bisect
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
from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind, NoteReason
from clearmd.backend.services.conversion.tex.context import (
    CITATION_MACROS,
    CODE_ENVIRONMENTS,
    REFERENCE_MACROS,
    Unparseable,
    make_context,
    mask,
    parse,
)
from clearmd.backend.services.conversion.tex.macros import (
    BudgetExceeded,
    DefinitionSite,
    MacroDefinition,
    MacroExpander,
    collect_definitions,
    definition_sites,
    is_parametrized_def,
    opens_or_closes_an_environment,
)
from clearmd.backend.services.conversion.tex.nodes import (
    MARK,
    argument,
    children,
    is_macro,
    raw,
    walk,
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
_INDENTATION = re.compile(r"\n[ \t]+")
# ClearMD marks the start of every block line it writes itself (headings, list markers, quotes,
# fences, math, table rows, footnotes); a final pass neutralizes any other line that Markdown
# would read as a block, and removes the marks. The mark is stripped from the input first, so a
# document cannot forge it (ADR-0023).
_FENCE_LINE = re.compile(r"[ \t]*" + MARK + r"(`{3,}|~{3,})(.*)")
_OWN_FENCE = re.compile(r"(`{3,}|~{3,})(.*)")
_SECTIONING_IN_BODY = re.compile(r"\\(" + "|".join(SECTION_LEVELS) + r")(?![A-Za-z@])")
_ENTITY = re.compile(r"&[#A-Za-z]")
# What Markdown reads as a block at the start of a line written by the document.
_BLOCK_LINE = re.compile(
    r"(?P<mark>#{1,6}(?=\s|$)|>|[-+*](?=\s|$)|(?P<number>\d{1,9})(?=[.)](?:\s|$))"
    r"|`{3,}|~{3,}|\||[=]+[ \t]*$|(?P<rule>[-*_])(?:[ \t]*(?P=rule)){2,}[ \t]*$)"
)
_TABLE_RULE = re.compile(r"\|?[ \t]*:?-+:?[ \t]*(\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*")
_MATH_TAG = re.compile(r"<(?=[A-Za-z/!?])")
_SAFE_LINK = re.compile(r"^(?:https?|ftp|mailto):|^[^:]*$", re.IGNORECASE)

INLINE = {
    "textbf": "**{}**",
    "textit": "*{}*",
    "textsl": "*{}*",
    "emph": "*{}*",
    "underline": "<u>{}</u>",
}
PLAIN = frozenset(
    {"textrm", "textsf", "textsc", "textup", "textmd", "textnormal", "mbox", "hbox", "text"}
)
# Layout and definitions: nothing to show (definitions are expanded by macros.py). Their arguments
# are declared in context.py, so they go with them.
DROPPED = frozenset(
    {
        "label", "index", "vspace", "hspace", "newpage", "clearpage", "cleardoublepage",
        "noindent", "centering", "tableofcontents", "listoffigures", "listoftables", "medskip",
        "bigskip", "smallskip", "vfill", "hfill", "linebreak", "pagebreak", "nopagebreak",
        "raggedright", "raggedleft", "documentclass", "usepackage", "graphicspath",
        "bibliographystyle", "bibliography", "printbibliography", "addbibresource", "pagestyle",
        "thispagestyle", "setlength", "setcounter", "addcontentsline", "phantomsection",
        "frontmatter", "mainmatter", "backmatter", "appendix", "thanks", "newcommand",
        "renewcommand", "providecommand", "DeclareMathOperator", "makeatletter", "makeatother",
        "small", "footnotesize", "large", "Large", "LARGE", "normalsize", "tiny", "huge", "Huge",
        "scriptsize", "bfseries", "itshape", "rmfamily", "sffamily", "ttfamily",
        "selectlanguage", "setmainlanguage", "onehalfspacing", "doublespacing", "singlespacing",
        "nocite", "hline", "toprule", "midrule", "bottomrule", "cline", "cmidrule", "today",
    }
)  # fmt: skip
METADATA = frozenset({"title", "author", "date"})
WORDS = {"LaTeXe": "LaTeX2e"}  # latex2text knows \LaTeX and \TeX
SPECIALS = {"~": " ", "--": "–", "---": "—", "``": "“", "''": "”", "!`": "¡", "?`": "¿"}
INCLUDES = frozenset({"input", "include", "subfile"})

LISTS = frozenset({"itemize", "enumerate", "description"})
QUOTES = frozenset({"quote", "quotation", "verse"})
CODE = frozenset(CODE_ENVIRONMENTS)
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
CONTAINERS = frozenset({"center", "flushleft", "flushright", "document"})
FLOATS = frozenset({"figure", "figure*", "wrapfigure", "table", "table*", "subfigure", "subtable"})
TABULARS = frozenset({"tabular", "tabular*", "tabularx", "longtable"})
LANGUAGES = frozenset(
    {
        "spanish", "english", "british", "american", "usenglish", "ukenglish", "french",
        "german", "ngerman", "italian", "portuguese", "brazil", "brazilian", "catalan",
        "basque", "galician",
    }
)  # fmt: skip
MAX_SUBSTITUTION_ROUNDS = 4  # \\myeq → \\bal → \\begin{align}: chains are short
MAX_UNKNOWN = 1000  # distinct names kept for the note; the text keeps every one as written

_LATEX2TEXT = LatexNodes2Text(math_mode="verbatim", strict_latex_spaces=False)
_LATEX2TEXT_DB = get_default_latex_context_db()

# The link target for an image argument, or ``None`` when it must not become a link (ADR-0022).
ImageHandler = Callable[[str], str | None]
# "file, line N" for a position of the source (documents made of several files).
Locator = Callable[[int], str]


def _block(text: str) -> str:
    return f"\n\n{text.strip(chr(10))}\n\n"


def _fence(code: str) -> str:
    longest = max((len(run) for run in re.findall("`+", code)), default=0)
    return "`" * max(3, longest + 1)


def _inline_code(code: str) -> str:
    if "`" not in code:
        return f"`{code}`"
    ticks = "`" * (max(len(run) for run in re.findall("`+", code)) + 1)
    return f"{ticks} {code} {ticks}"


def _indent(text: str, width: int) -> str:
    lines = text.split("\n")
    return "\n".join([lines[0], *[(" " * width + line) if line else "" for line in lines[1:]]])


def outside_code(text: str, fix: Callable[[str], str], *, blank_around: bool = False) -> str:
    """``fix`` applied to the text between fenced code blocks; the blocks stay as they are.

    A line scanner (linear): a fence closes on a line of the same character, at least as long,
    with nothing else on it (CommonMark); an unclosed fence runs to the end.
    """
    pieces: list[tuple[bool, list[str]]] = [(False, [])]
    fence: str | None = None
    for line in text.split("\n"):
        found = _FENCE_LINE.fullmatch(line)
        if (
            fence is None
            and found is not None
            and not (found.group(1)[0] == "`" and "`" in found.group(2))
        ):
            fence = found.group(1)
            pieces.append((True, [line]))
        elif fence is not None:
            pieces[-1][1].append(line)
            run = found.group(1) if found is not None and not found.group(2).strip() else ""
            if run and run[0] == fence[0] and len(run) >= len(fence):
                fence = None
                pieces.append((False, []))
        else:
            pieces[-1][1].append(line)
    if not blank_around:
        return "\n".join(
            "\n".join(lines) if is_code else fix("\n".join(lines)) for is_code, lines in pieces
        )
    # Exactly one blank line between a code block and the text around it.
    parts = [
        "\n".join(lines) if is_code else fix("\n".join(lines)).strip("\n")
        for is_code, lines in pieces
    ]
    return "\n\n".join(part for part in parts if part)


def escape_text(text: str) -> str:
    """Text from the document never becomes a link, an image or raw HTML (blocks: neutralize)."""
    return text.replace("<", "&lt;").replace("[", "&#91;").replace("]", "&#93;")


def escape_math(text: str) -> str:
    """``<img`` inside math is HTML to a viewer without math support; ``< img`` is the same math."""
    return _MATH_TAG.sub("< ", text)


def _marked(text: str) -> str:
    """``text``'s lines, each marked as written by ClearMD."""
    return "\n".join(MARK + line for line in text.split("\n"))


def _neutral_line(line: str, after_blank: bool) -> str:
    indent = len(line) - len(line.lstrip(" \t"))
    content = line[indent:]
    if after_blank and indent >= 4:  # an indented code block
        indent, line = 0, content
    if indent >= 4 or not content:
        return line
    if _TABLE_RULE.fullmatch(content) and "|" in content:
        return line[:indent] + "\\" + content
    found = _BLOCK_LINE.match(content)
    if found is None:
        return line
    if found.group("number") is not None:
        digits = found.group("number")
        return line[:indent] + digits + "\\" + content[len(digits) :]
    if content[0] == "<":
        return line[:indent] + "&lt;" + content[1:]
    return line[:indent] + "\\" + content


def neutralize(text: str, *, keep_marks: bool = False) -> str:
    """Every line the document wrote that Markdown would read as a block becomes plain text;
    ClearMD's own marked lines (and the code inside its fences) stay; the marks go (or stay,
    for a part that is marked again as a whole: a list item, a quote)."""
    out: list[str] = []
    fence: str | None = None
    after_blank = True
    for line in text.split("\n"):
        stripped = line.lstrip(" \t")
        if stripped.startswith(MARK):
            own = _OWN_FENCE.match(stripped[1:])
            if fence is None and own is not None:
                fence = own.group(1)
            elif fence is not None and own is not None and not own.group(2).strip():
                if own.group(1)[0] == fence[0] and len(own.group(1)) >= len(fence):
                    fence = None
            out.append(line if keep_marks else line.replace(MARK, ""))
        elif fence is not None:
            out.append(line)  # code, as written
        else:
            out.append(_neutral_line(line, after_blank))
        after_blank = not line.strip()
    joined = "\n".join(out)
    return joined if keep_marks else joined.replace(MARK, "")


def link_target(path: str) -> str:
    """A Markdown link destination that stays one destination whatever ``path`` holds."""
    if not re.search(r"[\s()<>]", path):
        return path
    return "<" + path.replace("<", "%3C").replace(">", "%3E") + ">"


def _is_label(node: Any) -> bool:
    return is_macro(node, "label")


def _is_float(node: Any) -> bool:
    if not isinstance(node, LatexEnvironmentNode):
        return False
    if node.environmentname in FLOATS:
        return True
    return node.environmentname == "minipage" and _own_caption(node) is not None


def _own_caption(node: Any) -> Any:
    """The first ``\\caption`` of a float, not looking into the floats inside it."""
    for found in walk(node.nodelist, skip=_is_float):
        if is_macro(found, "caption"):
            return found
    return None


def _body(nodes: list[Any]) -> tuple[list[Any], list[Any]]:
    """The preamble and the body (everything, when there is no ``document`` environment)."""
    for index, node in enumerate(nodes):
        if isinstance(node, LatexEnvironmentNode) and node.environmentname == "document":
            return nodes[:index], list(node.nodelist or [])
    return nodes, nodes


def top_level(nodes: list[Any], definitions: dict[str, MacroDefinition] | None = None) -> int:
    """The shallowest sectioning command really used (comments and code are separate nodes),
    also inside the author's macros that are used (``\\mychap`` → ``\\chapter``)."""
    _, body = _body(nodes)
    used: set[str] = set()
    present = []
    for node in walk(body):
        if isinstance(node, LatexMacroNode):
            if node.macroname in SECTION_LEVELS:
                present.append(SECTION_LEVELS[node.macroname])
            elif definitions and node.macroname in definitions:
                used.add(node.macroname)
    for name in used:
        assert definitions is not None
        present.extend(
            SECTION_LEVELS[n] for n in _SECTIONING_IN_BODY.findall(definitions[name].body)
        )
    return min(present, default=SECTION_LEVELS["section"])


def _options(node: Any, index: int) -> list[str]:
    return [option.strip() for option in raw(argument(node, index)).split(",") if option.strip()]


def is_spanish(nodes: list[Any]) -> bool:
    """babel's main language (its last option, else the class's) or polyglossia's is Spanish."""
    preamble, _ = _body(nodes)
    babel: list[str] = []
    global_options: list[str] = []
    main = ""
    for node in walk(preamble):
        if is_macro(node, "usepackage") and "babel" in _options(node, 1):
            babel = _options(node, 0) or babel
            chosen = [o.split("=", 1)[1] for o in babel if o.replace(" ", "").startswith("main=")]
            main = chosen[-1].strip() if chosen else main
        elif is_macro(node, "documentclass"):
            global_options = _options(node, 0)
        elif is_macro(node, "setmainlanguage") or is_macro(node, "setdefaultlanguage"):
            main = raw(argument(node, -1)).strip()
    if not main and babel:
        main = babel[-1]
    elif not main:
        languages = [o for o in global_options if o.lower() in LANGUAGES]
        main = languages[-1] if languages else ""
    return main.lower().startswith(("spanish", "español"))


class Renderer:
    def __init__(
        self,
        *,
        level: int = SECTION_LEVELS["section"],
        spanish: bool = False,
        image: ImageHandler | None = None,
        macros: MacroExpander | None = None,
        known_refused: frozenset[str] = frozenset(),
        listed: int = 0,
    ) -> None:
        self._top_level = level
        self._spanish = spanish
        self._image = image or (lambda path: path)
        self._macros = macros
        self.unknown: dict[str, None] = {}
        self.refused: dict[NoteItem, None] = {}
        self.tables_kept = 0
        self.footnotes: list[str] = []
        self.metadata: dict[str, list[Any]] = {}
        self._consumed: set[int] = set()  # captions already shown by their float
        self._alt: list[str] = []  # the caption of the float whose only image is being drawn
        self._known_refused = known_refused  # includes already noted while reading
        self._listed = listed  # how many of them: the note lists at most MAX_UNKNOWN
        self._in_code = 0  # inside \\texttt: text as written, no escaping, no ligatures
        self.recovered: dict[str, None] = {}  # what went wrong and was kept as written

    # --- Entry points -------------------------------------------------------------------------

    def document(self, nodes: list[Any]) -> str:
        preamble, body = _body(nodes)
        if body is not preamble:
            for node in walk(preamble):
                if isinstance(node, LatexMacroNode) and node.macroname in METADATA:
                    self.metadata[node.macroname] = self._last_arg(node)
        text = self.render(body)
        if self.footnotes:
            notes = "\n".join(
                f"{MARK}[^{n}]: {note}" for n, note in enumerate(self.footnotes, start=1)
            )
            text += _block(notes)
        return _tidy(text)

    def render(self, nodes: list[Any]) -> str:
        parts: list[str] = []
        after_unknown = False
        for node in self._without_false(nodes):
            if node is None:
                continue
            if after_unknown and isinstance(node, LatexGroupNode):
                parts.append(self._esc(node.latex_verbatim()))  # its arguments, as written
                continue
            before = len(self.unknown)
            piece = self._node(node)
            if isinstance(node, LatexCharsNode) and _ends_a_line(parts):
                piece = piece.lstrip(" \t")  # "\\section{A}    Text" is not a code block
            parts.append(piece)
            after_unknown = isinstance(node, LatexMacroNode) and len(self.unknown) > before
        return "".join(parts)

    def _without_false(self, nodes: list[Any]) -> list[Any]:
        """``nodes`` without what ``\\iffalse … \\fi`` comments out (nested conditionals
        counted); an ``\\iffalse`` without its ``\\fi`` hides nothing and is noted."""
        kept: list[Any] = []
        index = 0
        while index < len(nodes):
            node = nodes[index]
            if is_macro(node, "iffalse"):
                closing = _matching_fi(nodes, index + 1)
                if closing is not None:
                    index = closing + 1
                    continue
                self.recovered["\\iffalse without its \\fi"] = None
            kept.append(node)
            index += 1
        return kept

    def inline(self, nodes: list[Any]) -> str:
        return re.sub(r"\s+,", ",", " ".join(self.render(nodes).split()))

    # --- Nodes ------------------------------------------------------------------------------

    def _node(self, node: Any) -> str:
        if isinstance(node, LatexCharsNode):
            if self._in_code:
                return str(node.chars)
            text = _INDENTATION.sub("\n", str(node.chars))  # never an indented code block
            return escape_text(text)
        if isinstance(node, LatexCommentNode):
            return ""
        if isinstance(node, LatexSpecialsNode):
            chars = str(node.specials_chars)
            return chars if self._in_code else SPECIALS.get(chars, chars)
        if isinstance(node, LatexGroupNode):
            return self.render(node.nodelist or [])
        if isinstance(node, LatexMathNode):
            return self._math(node)
        if isinstance(node, LatexMacroNode | LatexEnvironmentNode):
            try:
                if isinstance(node, LatexMacroNode):
                    return self._macro(node)
                return self._environment(node)
            except (BudgetExceeded, RecursionError, MemoryError):
                raise
            except Exception as problem:  # one bad command, not the whole document (AC-21)
                name = getattr(node, "macroname", None) or f"{{{node.environmentname}}}"
                self.recovered[f"\\{name}: {type(problem).__name__}"] = None
                return self._esc(node.latex_verbatim())
        return ""

    def _arg_nodes(self, node: Any, index: int) -> list[Any]:
        found = argument(node, index)
        if found is None:
            return []
        if isinstance(found, LatexGroupNode):
            return list(found.nodelist or [])
        return [found]

    def _last_arg(self, node: Any) -> list[Any]:
        return self._arg_nodes(node, -1)

    def _macro(self, node: Any) -> str:
        name: str = node.macroname
        if self._macros is not None and self._macros.knows(name):
            return self._expanded(node, self.render)
        if name in SECTION_LEVELS:
            level = 2 + max(0, SECTION_LEVELS[name] - self._top_level)
            return _block(MARK + "#" * min(6, level) + " " + self.inline(self._last_arg(node)))
        if name in INLINE:
            content = self.inline(self._last_arg(node))
            return INLINE[name].format(content) if content else ""
        if name == "texttt":
            self._in_code += 1
            try:
                content = self.inline(self._last_arg(node))
            finally:
                self._in_code -= 1
            return _inline_code(content) if content else ""
        if name in PLAIN:
            return self.render(self._last_arg(node))
        if name in METADATA:
            self.metadata[name] = self._last_arg(node)
            return ""
        if name == "maketitle":
            return self._title_block()
        if name in {"href", "url"}:
            return self._link(node)
        if name == "verb":
            code = getattr(node.nodeargd, "verbatim_text", None)
            return _inline_code(code) if code is not None else self._unknown("\\verb", node)
        if name == "footnote":
            self.footnotes.append(self.inline(self._last_arg(node)))
            return f"[^{len(self.footnotes)}]"
        if name in CITATION_MACROS:
            return self._citation(node)
        if name in REFERENCE_MACROS:
            return f"({self._esc(raw(argument(node, 0)).strip())})"
        if name == "includegraphics":
            return self._picture(node)
        if name == "caption":
            if id(node) in self._consumed:
                return ""
            return _block(f"*{self.inline(self._last_arg(node))}*")
        if name in INCLUDES:
            return self._include_left(node)
        if name == "def":
            return self._unknown("\\def", node) if is_parametrized_def(node) else ""
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
            return self._esc(str(_LATEX2TEXT.nodelist_to_text([node])))
        return self._unknown(f"\\{name}", node)

    def _environment(self, node: Any) -> str:
        name: str = node.environmentname
        if name == "comment":
            return ""
        if name in CONTAINERS or (name == "minipage" and not _is_float(node)):
            return self.render(node.nodelist or [])
        if name == "abstract":
            heading = "Resumen" if self._spanish else "Abstract"
            return _block(f"{MARK}## {heading}") + _block(self.render(node.nodelist or []))
        if name in LISTS:
            return _block(self._list(node))
        if name in QUOTES:
            body = neutralize(self.render(node.nodelist or []).strip(), keep_marks=True)
            quoted = (f"{MARK}> {line}" if line else f"{MARK}>" for line in body.split("\n"))
            return _block("\n".join(quoted))
        if name in CODE:
            return _block(self._code(node))
        if name in DISPLAY_MATH:
            return _block(_marked(f"$$\n{self._math_body(node.nodelist)}\n$$"))
        if name in ALIGNED:
            inner = ALIGNED[name]
            body = self._math_body(node.nodelist)
            return _block(_marked(f"$$\n\\begin{{{inner}}}\n{body}\n\\end{{{inner}}}\n$$"))
        if _is_float(node):
            return self._float(node)
        if name in TABULARS:
            return self._tabular(node)
        return self._unknown(f"\\begin{{{name}}}", node)

    def _unknown(self, label: str, node: Any) -> str:
        if label in self.unknown or len(self.unknown) < MAX_UNKNOWN:
            self.unknown[label] = None
        return self._esc(node.latex_verbatim())

    def _esc(self, text: str) -> str:
        """Document text copied as written: never a link or HTML (inside code, left as is)."""
        return text if self._in_code else escape_text(text)

    # --- Pieces -------------------------------------------------------------------------------

    def _title_block(self) -> str:
        title = self.inline(self.metadata.get("title", []))
        if not title:
            return ""
        byline = " · ".join(
            part
            for part in (self.inline(self.metadata.get(k, [])) for k in ("author", "date"))
            if part
        )
        return _block(f"{MARK}# {title}" + (f"\n\n{MARK}*{byline}*" if byline else ""))

    def _link(self, node: Any) -> str:
        url = raw(argument(node, 0)).strip()
        text = self.inline(self._arg_nodes(node, 1)) if node.macroname == "href" else ""
        # "javascript&#58;" is "javascript:" once a viewer decodes it.
        safe = bool(_SAFE_LINK.match(url)) and not _ENTITY.search(url)
        if node.macroname == "url":
            return f"<{url}>" if safe and not re.search(r"[\s<>]", url) else _inline_code(url)
        if not safe:  # javascript: and friends never become links
            return f"{text} ({_inline_code(url)})" if text else _inline_code(url)
        return f"[{text or url}]({link_target(url)})"

    def _citation(self, node: Any) -> str:
        written = self._esc(raw(argument(node, 3)))
        keys = [key.strip() for key in written.split(",") if key.strip()]
        if not keys:
            return ""
        first = self._esc(raw(argument(node, 1)).strip())
        second = self._esc(raw(argument(node, 2)).strip())
        before, after = (first, second) if argument(node, 2) is not None else ("", first)
        cited = "; ".join(f"@{key}" for key in keys)
        return (
            "[" + (f"{before} " if before else "") + cited + (f", {after}" if after else "") + "]"
        )

    def _math(self, node: Any) -> str:
        body = self._math_body(node.nodelist)
        if node.displaytype == "display":
            return _block(_marked(f"$$\n{body}\n$$"))
        return f"${body}$"

    def _math_body(self, nodes: list[Any] | None) -> str:
        return escape_math(" ".join(self._math_source(list(nodes or [])).split()))

    # --- Math as written, with the author's macros ----------------------------------------------

    def _expanded(
        self, node: Any, serialize: Callable[[list[Any]], str], *, math: bool = False
    ) -> str:
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
            written: str = node.latex_verbatim()
            return written if math else self._esc(written)

    def _math_source(self, nodes: list[Any]) -> str:
        return "".join(self._serialize(n) for n in nodes if n is not None and not _is_label(n))

    def _serialize(self, node: Any) -> str:
        """Math as written; only comments and spans that use an author's macro are replaced."""
        if isinstance(node, LatexCommentNode):
            return " "  # "% first\nc &= d" must not hide "c &= d" once lines are joined
        verbatim: str = node.latex_verbatim()
        if isinstance(node, LatexMacroNode) and self._knows(node.macroname):
            text = self._expanded(node, self._math_source, math=True)
            # "\\R x" must not become "\\mathbb{R}x" glued to a following letter by mistake.
            if text != verbatim and _CONTROL_WORD_AT_END.search(text):
                text += " "
            return text
        inner = children(node)
        if not any(self._needs_rewrite(child) for child in inner):
            return verbatim
        source: str = node.parsing_state.s
        parts, cursor = [], node.pos
        for child in inner:
            parts.append(source[cursor : child.pos])
            parts.append(self._serialize(child))
            cursor = child.pos + child.len
        parts.append(source[cursor : node.pos + node.len])
        return "".join(parts)

    def _knows(self, name: str) -> bool:
        return self._macros is not None and self._macros.knows(name)

    def _needs_rewrite(self, node: Any) -> bool:
        return any(
            isinstance(found, LatexCommentNode)
            or (isinstance(found, LatexMacroNode) and self._knows(found.macroname))
            for found in walk([node])
        )

    # --- Blocks -------------------------------------------------------------------------------

    def _list(self, node: Any) -> str:
        before: list[Any] = []
        items: list[tuple[Any, list[Any]]] = []
        for child in self._without_false(list(node.nodelist or [])):
            if is_macro(child, "item"):
                items.append((child, []))
            elif items:
                items[-1][1].append(child)
            else:
                before.append(child)
        lines = []
        for number, (item, content) in enumerate(items, start=1):
            marker = f"{number}. " if node.environmentname == "enumerate" else "- "
            text = self.render(content).strip()
            if node.environmentname == "description":
                term = self.inline(self._arg_nodes(item, 0))
                text = f"**{term}** {text}" if term else text
            # Tight items, nested lists included; code inside an item keeps its blank lines.
            text = outside_code(text, lambda part: re.sub(r"\n[ \t]*\n+", "\n", part))
            text = neutralize(text, keep_marks=True)  # "\\item # x" is not a heading in an item
            lines.append(MARK + marker + _indent(text, len(marker)))
        intro = self.render(before).strip()
        listed = "\n".join(lines)
        return f"{intro}\n\n{listed}" if intro else listed

    def _code(self, node: Any) -> str:
        found = getattr(node.nodeargd, "verbatim_text", None) if node.nodeargd else None
        code_text: str = found or ""
        language = ""
        if node.environmentname == "lstlisting":
            options = re.match(r"\s*\[([^\]\n]{0,1024})\]", code_text)
            if options:
                code_text = code_text[options.end() :]
                declared = re.search(r"language\s*=\s*\{?([\w+#-]+)", options.group(1))
                language = declared.group(1).lower() if declared else ""
        elif node.environmentname == "minted":
            declared = re.match(r"\s*(?:\[[^\]\n]{0,1024}\])?\s*\{([^}\n]{0,64})\}", code_text)
            if declared:
                code_text = code_text[declared.end() :]
                language = declared.group(1).strip().lower()
        code = code_text.strip("\n")
        fence = _fence(code)
        return f"{MARK}{fence}{language}\n{code}\n{MARK}{fence}"

    def _picture(self, node: Any) -> str:
        path = raw(argument(node, -1)).strip()
        target = self._image(path)
        if target is None:  # outside the folder or remote: shown, never fetched by a viewer
            return _inline_code(node.latex_verbatim().strip())
        alt = self._alt[-1] if self._alt else ""
        return f"![{alt}]({link_target(target)})"

    def _float(self, node: Any) -> str:
        """A figure or table: its content in order; the caption on its only image, or under it."""
        caption_node = _own_caption(node)
        caption = self.inline(self._last_arg(caption_node)) if caption_node is not None else ""
        if caption_node is not None:
            self._consumed.add(id(caption_node))
        images = [n for n in walk(node.nodelist, skip=_is_float) if is_macro(n, "includegraphics")]
        if len(images) == 1 and caption:
            self._alt.append(caption)
            try:
                return _block(self.render(node.nodelist or []))
            finally:
                self._alt.pop()
        self._alt.append("")
        try:
            body = self.render(node.nodelist or [])
        finally:
            self._alt.pop()
        return _block(body) + (_block(f"*{caption}*") if caption else "")

    def _tabular(self, node: Any) -> str:
        captions = [child for child in node.nodelist or [] if is_macro(child, "caption")]
        self._consumed.update(id(caption) for caption in captions)
        caption = self.inline(self._last_arg(captions[0])) if captions else ""
        table = tabular_to_markdown(node, self.inline)
        if table is None:
            self.tables_kept += 1
            source = node.latex_verbatim()
            fence = _fence(source)
            table = f"{MARK}{fence}latex\n{source}\n{MARK}{fence}"
        return _block(table) + (_block(f"*{caption}*") if caption else "")

    def _include_left(self, node: Any) -> str:
        """An include still in the text: refused while reading (noted there) or made by a macro."""
        subject = raw(argument(node, 0)).strip()
        if self._listed + len(self.refused) < MAX_UNKNOWN:
            if self._macros is not None and self._macros.depth > 0:
                self.refused[NoteItem(subject, NoteReason.MADE_BY_MACRO.value)] = None
            elif subject not in self._known_refused:  # "\\input{{ch}}": no file has that name
                self.refused[NoteItem(subject, NoteReason.MISSING.value)] = None
        return _inline_code(node.latex_verbatim().strip())

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


_CONDITIONAL_NAME = re.compile(r"if(?!thenelse)[A-Za-z@]*")


def _matching_fi(nodes: list[Any], start: int) -> int | None:
    r"""The index of the sibling ``\fi`` closing a conditional opened before ``start``."""
    depth = 1
    for index in range(start, len(nodes)):
        node = nodes[index]
        if isinstance(node, LatexMacroNode):
            if node.macroname == "fi":
                depth -= 1
                if depth == 0:
                    return index
            elif _CONDITIONAL_NAME.fullmatch(node.macroname):
                depth += 1
    return None


def _ends_a_line(parts: list[str]) -> bool:
    for part in reversed(parts):
        if part:
            return part.endswith("\n")
    return False


def _tidy(text: str) -> str:
    def tidy(part: str) -> str:
        # Trailing spaces go, except a hard line break ("  ") after real text.
        lines = [
            line if line.endswith("  ") and line.strip() else line.rstrip()
            for line in part.split("\n")
        ]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines))

    return outside_code(text, tidy, blank_around=True).strip() + "\n"


def _expander(nodes: list[Any], source_size: int) -> tuple[MacroExpander | None, bool]:
    """The author's macros, and whether the source must be parsed again with their arguments."""
    definitions = collect_definitions(nodes)
    if not definitions:
        return None, False
    base = make_context()
    again = any(
        definition.arguments or base.get_macro_spec(name) is not None
        for name, definition in definitions.items()
    )
    return MacroExpander(definitions, source_size), again


def _substitute_round(
    text: str, nodes: list[Any], macros: MacroExpander
) -> tuple[str, list[tuple[int, int, int, int]]] | None:
    """One round of text substitution of structural macros, in document order (each use takes
    the definition in force where it is written). ``None`` when there is nothing to do."""
    sites = definition_sites(nodes)
    structural = {
        site.name
        for site in sites
        if site.name and site.definition and opens_or_closes_an_environment(site.definition)
    }
    if not structural:
        return None
    by_name: dict[str, list[DefinitionSite]] = {}
    for site in sites:
        if site.name in structural:
            by_name.setdefault(site.name, []).append(site)
    heads = sorted((site.head_start, site.head_end) for site in sites)
    head_starts = [start for start, _ in heads]
    names = "|".join(re.escape(name) for name in sorted(structural, key=len, reverse=True))
    use = re.compile(r"\\(" + names + r")(?![A-Za-z@])")
    pieces: list[str] = []
    moved: list[tuple[int, int, int, int]] = []  # new start, new end, old start, old end
    cursor = length = 0
    for found in use.finditer(mask(text)):
        at = bisect.bisect_right(head_starts, found.start()) - 1
        if at >= 0 and found.start() < heads[at][1]:
            continue  # the name being defined, never a use
        defined = [site for site in by_name[found.group(1)] if site.head_start < found.start()]
        definition = defined[-1].definition if defined else None
        if definition is None or not opens_or_closes_an_environment(definition):
            continue
        try:
            macros.charge(found.group(1), len(definition.body))
        except BudgetExceeded:
            break
        before = text[cursor : found.start()]
        pieces.append(before)
        length += len(before)
        replacement = definition.body + " "
        moved.append((length, length + len(replacement), found.start(), found.end()))
        pieces.append(replacement)
        length += len(replacement)
        cursor = found.end()
    if not moved:
        return None
    pieces.append(text[cursor:])
    return "".join(pieces), moved


def _substitute_structural(
    text: str, nodes: list[Any], macros: MacroExpander
) -> tuple[str, list[Any], Callable[[int], int]] | None:
    r"""Uses of ``\beq`` → ``\begin{equation}`` in the text itself, as TeX does, so that the
    environment they open takes the text up to the macro that closes it. Repeated while a round
    makes new uses appear (``\myeq`` → ``\bal`` → ``\begin{align}``, or inside a body); never
    inside a definition's head, a comment or code; charged to the budget like any expansion."""
    rounds: list[list[tuple[int, int, int, int]]] = []
    for _ in range(MAX_SUBSTITUTION_ROUNDS):
        done = _substitute_round(text, nodes, macros)
        if done is None:
            break
        text, moved = done
        rounds.append(moved)
        nodes, _ = parse(text, make_context())
    if not rounds:
        return None

    def original(position: int) -> int:
        for moved in reversed(rounds):
            index = bisect.bisect_right([m[0] for m in moved], position) - 1
            if index < 0:
                continue
            new_start, new_end, old_start, old_end = moved[index]
            position = old_start if position < new_end else old_end + (position - new_end)
        return position

    return text, nodes, original


def _kept_as_latex(text: str, cause: str, refused: tuple[NoteItem, ...]) -> ConversionResult:
    fence = _fence(text)
    markdown = f"{fence}latex\n{text.strip(chr(10))}\n{fence}\n"
    notes = [
        ConversionNote(NoteKind.PARSE_RECOVERED, (NoteItem(cause, NoteReason.KEPT_AS_LATEX.value),))
    ]
    if refused:
        notes.insert(0, ConversionNote(NoteKind.INCLUDE_NOT_FOLLOWED, refused))
    return ConversionResult(markdown, tuple(notes))


def render_source(
    text: str,
    *,
    image: ImageHandler | None = None,
    locate: Locator | None = None,
    refused: tuple[NoteItem, ...] = (),
) -> ConversionResult:
    """Markdown and notes for a whole LaTeX source (its includes already in place).

    Whatever happens inside, the file is converted: at worst kept whole as LaTeX (AC-21).
    """
    text = text.replace(MARK, "")  # the document can never forge ClearMD's own block marks
    try:
        nodes, error = parse(text, make_context())
        macros, again = _expander(nodes, len(text))
        if macros is not None:
            substituted = _substitute_structural(text, nodes, macros)
            if substituted is not None:
                text, nodes, original = substituted
                if locate is not None:
                    locate = _through(locate, original)
                remaining = {
                    name: definition
                    for name, definition in collect_definitions(nodes).items()
                    if not opens_or_closes_an_environment(definition)  # uses already in place
                }
                macros.redefine(remaining)
                again = True
            if again:
                nodes, error = parse(text, macros.context)
        renderer = Renderer(
            level=top_level(nodes, macros.definitions if macros is not None else None),
            spanish=is_spanish(nodes),
            image=image,
            macros=macros,
            known_refused=frozenset(item.subject for item in refused),
            listed=len(refused),
        )
        markdown = neutralize(renderer.document(nodes))
    except MemoryError:
        raise  # the worker reports it as out of memory
    except (Unparseable, RecursionError) as problem:
        cause = str(problem) if isinstance(problem, Unparseable) else type(problem).__name__
        return _kept_as_latex(text, cause, refused)
    except Exception as problem:  # a converter bug must not lose a thesis (AC-21)
        return _kept_as_latex(text, type(problem).__name__, refused)
    notes = list(renderer.notes())
    not_followed = (*refused, *renderer.refused)
    if not_followed:
        notes.append(ConversionNote(NoteKind.INCLUDE_NOT_FOLLOWED, not_followed))
    recovered = [NoteItem(problem) for problem in renderer.recovered]
    if error is not None:
        place = f"{locate(error.position)}: " if locate is not None else ""
        recovered.insert(0, NoteItem(place + error.message))
    if recovered:
        notes.append(ConversionNote(NoteKind.PARSE_RECOVERED, tuple(recovered)))
    return ConversionResult(markdown, tuple(notes))


def _through(locate: Locator, original: Callable[[int], int]) -> Locator:
    return lambda position: locate(original(position))


def render_latex(text: str) -> ConversionResult:
    """Convert one LaTeX source on its own (no includes followed: see ``convert_document``)."""
    return render_source(text)
