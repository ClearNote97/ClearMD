r"""LaTeX nodes → Markdown: the supported subset of spec 002, everything else kept and reported.

Text-mode nodes follow the subset table; math is re-serialized as written (comments dropped, the
author's macros expanded); a command that neither this renderer nor pylatexenc's ``latex2text``
knows is written back as is and listed in a note. A source pylatexenc cannot read at all (deep
nesting) is kept whole as a LaTeX code block, with a note: a file never fails as a whole (AC-21).
"""

import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
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
from clearmd.backend.services.conversion.markdown_out import (
    ENTITY,
    MARK,
    SAFE_LINK,
    block,
    ends_a_line,
    escape_math,
    escape_text,
    fence_for,
    indent,
    inline_code,
    join_pieces,
    link_target,
    math_line,
    neutralize,
    outside_code,
    tidy,
)
from clearmd.backend.services.conversion.tex.images import name_only_image
from clearmd.backend.services.conversion.tex.macros import (
    BudgetExceeded,
    MacroExpander,
    build_expander,
    collect_definitions,
    is_parametrized_def,
    opens_or_closes_an_environment,
    substitute_structural,
)
from clearmd.backend.services.conversion.tex.nodes import (
    argument,
    children,
    is_macro,
    raw,
    walk,
)
from clearmd.backend.services.conversion.tex.parsing import (
    CITATION_MACROS,
    REFERENCE_MACROS,
    Unparseable,
    make_context,
    parse,
)
from clearmd.backend.services.conversion.tex.tables import tabular_to_markdown
from clearmd.backend.services.conversion.tex.writer.conditionals import matching_fi
from clearmd.backend.services.conversion.tex.writer.floats import is_float, own_caption
from clearmd.backend.services.conversion.tex.writer.math import is_label
from clearmd.backend.services.conversion.tex.writer.state import ImageHandler
from clearmd.backend.services.conversion.tex.writer.structure import (
    is_spanish,
    split_document,
    top_level,
)
from clearmd.backend.services.conversion.tex.writer.vocab import (
    ALIGNED,
    CODE,
    CONTAINERS,
    DISPLAY_MATH,
    DROPPED,
    INCLUDES,
    INLINE,
    LISTS,
    MAX_UNKNOWN,
    METADATA,
    PLAIN,
    QUOTES,
    SECTION_LEVELS,
    SPECIALS,
    TABULARS,
    WORDS,
)

_CONTROL_WORD_AT_END = re.compile(r"\\[A-Za-z]+$")
_INDENTATION = re.compile(r"\n[ \t]+")

_LATEX2TEXT = LatexNodes2Text(math_mode="verbatim", strict_latex_spaces=False)
_LATEX2TEXT_DB = get_default_latex_context_db()

# "file, line N" for a position of the source (documents made of several files).
Locator = Callable[[int], str]


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
        self._image = image or name_only_image
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
        preamble, body = split_document(nodes)
        if body is not preamble:
            for node in walk(preamble):
                if isinstance(node, LatexMacroNode) and node.macroname in METADATA:
                    self.metadata[node.macroname] = self._last_arg(node)
        text = self.render(body)
        if self.footnotes:
            notes = "\n".join(
                f"{MARK}[^{n}]: {note}" for n, note in enumerate(self.footnotes, start=1)
            )
            text += block(notes)
        return tidy(text)

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
            if isinstance(node, LatexCharsNode) and ends_a_line(parts):
                piece = piece.lstrip(" \t")  # "\\section{A}    Text" is not a code block
            parts.append(piece)
            after_unknown = isinstance(node, LatexMacroNode) and len(self.unknown) > before
        return join_pieces(parts)

    def _without_false(self, nodes: list[Any]) -> list[Any]:
        """``nodes`` without what ``\\iffalse … \\fi`` comments out (nested conditionals
        counted); an ``\\iffalse`` without its ``\\fi`` hides nothing and is noted."""
        kept: list[Any] = []
        index = 0
        while index < len(nodes):
            node = nodes[index]
            if is_macro(node, "iffalse"):
                closing = matching_fi(nodes, index + 1)
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
            return block(MARK + "#" * min(6, level) + " " + self.inline(self._last_arg(node)))
        if name in INLINE:
            content = self.inline(self._last_arg(node))
            return INLINE[name].format(content) if content else ""
        if name == "texttt":
            self._in_code += 1
            try:
                content = self.inline(self._last_arg(node))
            finally:
                self._in_code -= 1
            return inline_code(content) if content else ""
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
            return inline_code(code) if code is not None else self._unknown("\\verb", node)
        if name == "footnote":
            with self._text_mode():
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
            return block(f"*{self.inline(self._last_arg(node))}*")
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
        if name in CONTAINERS or (name == "minipage" and not is_float(node)):
            return self.render(node.nodelist or [])
        if name == "abstract":
            heading = "Resumen" if self._spanish else "Abstract"
            return block(f"{MARK}## {heading}") + block(self.render(node.nodelist or []))
        if name in LISTS:
            return block(self._list(node))
        if name in QUOTES:
            body = neutralize(self.render(node.nodelist or []).strip(), keep_marks=True)
            quoted = (f"{MARK}> {line}" if line else f"{MARK}>" for line in body.split("\n"))
            return block("\n".join(quoted))
        if name in CODE:
            return block(self._code(node))
        if name in DISPLAY_MATH:
            return block(self._display(self._math_body(node.nodelist)))
        if name in ALIGNED:
            inner = ALIGNED[name]
            body = self._math_body(node.nodelist)
            return block(self._display(f"\\begin{{{inner}}}\n{body}\n\\end{{{inner}}}"))
        if is_float(node):
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
        return text.replace(MARK, "") if self._in_code else escape_text(text)

    @contextmanager
    def _text_mode(self) -> Iterator[None]:
        """Text written somewhere else later (a footnote, a caption, the title) is never code,
        even when its command sits inside ``\\texttt``."""
        saved, self._in_code = self._in_code, 0
        try:
            yield
        finally:
            self._in_code = saved

    # --- Pieces -------------------------------------------------------------------------------

    def _title_block(self) -> str:
        with self._text_mode():
            return self._title_text()

    def _title_text(self) -> str:
        title = self.inline(self.metadata.get("title", []))
        if not title:
            return ""
        byline = " · ".join(
            part
            for part in (self.inline(self.metadata.get(k, [])) for k in ("author", "date"))
            if part
        )
        return block(f"{MARK}# {title}" + (f"\n\n{MARK}*{byline}*" if byline else ""))

    def _link(self, node: Any) -> str:
        url = raw(argument(node, 0)).strip()
        text = self.inline(self._arg_nodes(node, 1)) if node.macroname == "href" else ""
        # "javascript&#58;" is "javascript:" once a viewer decodes it.
        safe = bool(SAFE_LINK.match(url)) and not ENTITY.search(url)
        if node.macroname == "url":
            if not url:
                return ""
            # <…> is an autolink only with a scheme ("<texto>" would be an HTML tag); any other
            # \url is shown as code.
            absolute = re.match(r"(?:https?|ftp|mailto):", url, re.IGNORECASE)
            if safe and absolute and not re.search(r"[\s<>\x00-\x1f\x7f]", url):
                return f"<{url}>"
            return inline_code(url)
        if not url:
            return text
        if not safe:  # javascript: and friends never become links
            return f"{text} ({inline_code(url)})" if text else inline_code(url)
        return f"[{text or escape_text(url)}]({link_target(url)})"

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
            return block(self._display(body))
        return f"${body}$"

    def _display(self, body: str) -> str:
        """``$$`` lines are ClearMD's; the math between them is never read as Markdown blocks."""
        lines = "\n".join(math_line(line) for line in body.split("\n"))
        return f"{MARK}$$\n{lines}\n{MARK}$$"

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
        return "".join(self._serialize(n) for n in nodes if n is not None and not is_label(n))

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
            lines.append(MARK + marker + indent(text, len(marker)))
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
        fence = fence_for(code)
        return f"{MARK}{fence}{language}\n{code}\n{MARK}{fence}"

    def _picture(self, node: Any) -> str:
        path = raw(argument(node, -1)).strip()
        target = self._image(path)
        if target is None:  # outside the folder or remote: shown, never fetched by a viewer
            return inline_code(node.latex_verbatim().strip())
        alt = self._alt[-1] if self._alt else ""
        return f"![{alt}]({link_target(target)})"

    def _float(self, node: Any) -> str:
        """A figure or table: its content in order; the caption on its only image, or under it."""
        caption_node = own_caption(node)
        with self._text_mode():
            caption = self.inline(self._last_arg(caption_node)) if caption_node else ""
        if caption_node is not None:
            self._consumed.add(id(caption_node))
        images = [n for n in walk(node.nodelist, skip=is_float) if is_macro(n, "includegraphics")]
        if len(images) == 1 and caption:
            self._alt.append(caption)
            try:
                return block(self.render(node.nodelist or []))
            finally:
                self._alt.pop()
        self._alt.append("")
        try:
            body = self.render(node.nodelist or [])
        finally:
            self._alt.pop()
        return block(body) + (block(f"*{caption}*") if caption else "")

    def _tabular(self, node: Any) -> str:
        captions = [child for child in node.nodelist or [] if is_macro(child, "caption")]
        self._consumed.update(id(caption) for caption in captions)
        caption = self.inline(self._last_arg(captions[0])) if captions else ""
        table = tabular_to_markdown(node, self.inline)
        if table is None:
            self.tables_kept += 1
            source = node.latex_verbatim()
            fence = fence_for(source)
            table = f"{MARK}{fence}latex\n{source}\n{MARK}{fence}"
        return block(table) + (block(f"*{caption}*") if caption else "")

    def _include_left(self, node: Any) -> str:
        """An include still in the text: refused while reading (noted there) or made by a macro."""
        subject = raw(argument(node, 0)).strip()
        if self._listed + len(self.refused) < MAX_UNKNOWN:
            if self._macros is not None and self._macros.depth > 0:
                self.refused[NoteItem(subject, NoteReason.MADE_BY_MACRO.value)] = None
            elif subject not in self._known_refused:  # "\\input{{ch}}": no file has that name
                self.refused[NoteItem(subject, NoteReason.MISSING.value)] = None
        return inline_code(node.latex_verbatim().strip())

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


def _kept_as_latex(text: str, cause: str, refused: tuple[NoteItem, ...]) -> ConversionResult:
    fence = fence_for(text)
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
    # The document can never forge ClearMD's own block marks; every line ends with "\n" (a lone
    # "\r" is a line ending to CommonMark too).
    text = re.sub(r"\r\n?", "\n", text.replace(MARK, ""))
    try:
        nodes, error = parse(text, make_context())
        macros, again = build_expander(nodes, len(text))
        if macros is not None:
            substituted = substitute_structural(text, nodes, macros)
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
    return render_source(text, image=name_only_image)
