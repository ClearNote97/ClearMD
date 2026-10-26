"""OpenDocument text → Markdown: the subset of spec 003, written through ``markdown_out``.

A paragraph is flattened into runs of text with their effective properties (paragraph style,
spans and their parents), equal neighbours merged, and written with delimiters that open and
close as the properties change (``**a*b***``), spaces kept outside them. Everything outside the
subset keeps its text and is listed in a note. Images become placeholders; formulas, LaTeX.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind, NoteReason
from clearmd.backend.services.conversion.markdown_out import (
    ENTITY,
    MARK,
    SAFE_LINK,
    block,
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
from clearmd.backend.services.conversion.odt.styles import Role, Styles, TextProps
from clearmd.backend.services.conversion.odt.tables import table_to_markdown
from clearmd.backend.services.conversion.odt.xmltree import Element

LINE_BREAK = "  \n"
MAX_NOTES = 10_000
# What a document may make ClearMD write beyond its own size (repeated formulas, repeated table
# cells): the same rule as the author's macros in .tex (ADR-0022), 4x the text plus 1 MiB.
GROWTH_FACTOR = 4
GROWTH_EXTRA = 1024**2
IMAGE_WORD = {"es": "Imagen", "pt": "Imagem", "fr": "Image", "it": "Immagine", "de": "Bild"}
FORMULA_WORD = {"es": "Fórmula", "pt": "Fórmula", "fr": "Formule", "it": "Formula", "de": "Formel"}
MAX_SPACES = 256
MAX_UNKNOWN = 1000
_WHITESPACE = re.compile(r"[ \t\r\n]+")

# Field elements: what matters is the text they show.
FIELDS = frozenset(
    {
        "text:page-number", "text:page-count", "text:page-continuation", "text:date", "text:time",
        "text:author-name", "text:author-initials", "text:creator", "text:title", "text:subject",
        "text:description", "text:keywords", "text:initial-creator", "text:creation-date",
        "text:creation-time", "text:modification-date", "text:modification-time",
        "text:print-date", "text:print-time", "text:printed-by", "text:editing-cycles",
        "text:editing-duration", "text:chapter", "text:file-name", "text:template-name",
        "text:sequence", "text:sequence-ref", "text:reference-ref", "text:bookmark-ref",
        "text:note-ref", "text:variable-get", "text:variable-set", "text:variable-input",
        "text:user-field-get", "text:user-field-input", "text:user-defined", "text:expression",
        "text:text-input", "text:placeholder", "text:conditional-text", "text:database-display",
        "text:sheet-name", "text:meta", "text:meta-field", "text:measure", "text:table-formula",
    }
)  # fmt: skip
# Inline elements with nothing to show (layout, anchors, marks, revisions handled apart).
DROPPED_INLINE = frozenset(
    {
        "text:soft-page-break", "text:bookmark", "text:bookmark-start", "text:bookmark-end",
        "text:reference-mark", "text:reference-mark-start", "text:reference-mark-end",
        "text:toc-mark", "text:toc-mark-start", "text:toc-mark-end", "text:alphabetical-index-mark",
        "text:alphabetical-index-mark-start", "text:alphabetical-index-mark-end",
        "text:user-index-mark", "text:user-index-mark-start", "text:user-index-mark-end",
        "text:bibliography-mark", "text:change", "text:change-start", "text:change-end",
        "office:annotation-end", "text:number", "text:hidden-paragraph",
    }
)  # fmt: skip
# Block elements with nothing to show: declarations, forms, generated indexes.
DROPPED_BLOCKS = frozenset(
    {
        "text:sequence-decls", "text:variable-decls", "text:user-field-decls",
        "text:dde-connection-decls", "office:forms", "text:soft-page-break",
        "text:table-of-content", "text:illustration-index", "text:table-index",
        "text:object-index", "text:user-index", "text:alphabetical-index", "text:bibliography",
        "table:table-columns", "table:table-column", "text:bookmark", "text:bookmark-start",
        "text:bookmark-end", "text:change", "text:change-start", "text:change-end",
        "text:hidden-paragraph",
    }
)  # fmt: skip
SPAN_LIKE = frozenset({"text:span"})


@dataclass(frozen=True)
class _Text:
    text: str
    props: TextProps
    link: str | None
    literal: bool = False  # spaces and tabs written as such (text:s, text:tab): never collapsed


@dataclass(frozen=True)
class _Raw:
    markdown: str  # written by ClearMD itself: a footnote reference, a line break, a placeholder


_Piece = _Text | _Raw
_ORDER = ("bold", "italic", "strike", "underline", "position")
_OPEN = {"bold": "**", "italic": "*", "strike": "~~", "underline": "<u>"}
_CLOSE = {"bold": "**", "italic": "*", "strike": "~~", "underline": "</u>"}


def _active(props: TextProps) -> list[str]:
    found = []
    for key in _ORDER:
        value = getattr(props, key)
        if value:
            found.append(f"position:{value}" if key == "position" else key)
    return found


_POSITION_TAG = {"super": "sup", "sub": "sub"}


def _opener(key: str) -> str:
    if key.startswith("position:"):
        return f"<{_POSITION_TAG[key.split(':')[1]]}>"
    return _OPEN[key]


def _closer(key: str) -> str:
    if key.startswith("position:"):
        return f"</{_POSITION_TAG[key.split(':')[1]]}>"
    return _CLOSE[key]


# A formula object and whether it is alone in its paragraph → its LaTeX (without $), or ``None``
# with the source to show instead (StarMath, or nothing) when it is not converted.
FormulaHandler = Callable[[Element], "FormulaResult"]


@dataclass(frozen=True)
class FormulaResult:
    latex: str | None
    source: str | None = None


@dataclass
class _Counts:
    images: int = 0
    formulas_kept: int = 0
    comments: int = 0
    changes: int = 0
    tables_simplified: int = 0
    unknown: dict[str, None] = field(default_factory=dict)


class OdtRenderer:
    def __init__(
        self,
        styles: Styles,
        *,
        formula: FormulaHandler | None = None,
        language: str = "",
        source_size: int = 0,
    ) -> None:
        self.styles = styles
        self._room = GROWTH_FACTOR * source_size + GROWTH_EXTRA
        self.counts = _Counts()
        self.footnotes: list[str] = []
        self._formula = formula
        primary = (language or styles.language).split("-")[0]
        self._image_word = IMAGE_WORD.get(primary, "Image")
        self._formula_word = FORMULA_WORD.get(primary, "Formula")
        self._top = 1

    # --- Document -------------------------------------------------------------------------

    def document(self, content: Element) -> str:
        body = content.find("office:body")
        text = body.find("office:text") if body is not None else None
        if text is None:
            return ""
        levels = [
            int(h.get("text:outline-level")) for h in text.walk()
            if h.tag == "text:h" and h.get("text:outline-level").isdigit()
        ]  # fmt: skip
        self._top = min(levels, default=1)
        rendered = self.blocks(list(text.elements()))
        if self.footnotes:
            notes = "\n".join(
                f"{MARK}[^{n}]: {note}" for n, note in enumerate(self.footnotes, start=1)
            )
            rendered += block(notes)
        return neutralize(tidy(rendered))

    def blocks(self, elements: list[Element]) -> str:
        parts: list[str] = []
        index = 0
        while index < len(elements):
            element = elements[index]
            role = self._role(element)
            if role in {Role.QUOTE, Role.CODE}:
                run = [element]
                while index + 1 < len(elements) and self._role(elements[index + 1]) is role:
                    index += 1
                    run.append(elements[index])
                parts.append(self._quote(run) if role is Role.QUOTE else self._code(run))
            else:
                parts.append(self._block(element))
            index += 1
        return "".join(parts)

    def _role(self, element: Element) -> Role | None:
        if element.tag != "text:p":
            return None
        return self.styles.role(element.get("text:style-name"))

    def _block(self, element: Element) -> str:
        tag = element.tag
        if tag == "text:p":
            return self._paragraph(element)
        if tag == "text:h":
            return self._heading(element)
        if tag == "text:list":
            return block(self._list(element, 1, ""))
        if tag == "table:table":
            return self._table(element)
        if tag == "text:section":
            if element.get("text:display") == "none":
                return ""
            return self.blocks(list(element.elements()))
        if tag == "text:tracked-changes":
            self.counts.changes += sum(1 for _ in element.elements("text:changed-region"))
            return ""
        if tag in DROPPED_BLOCKS:
            return ""
        self._unknown(tag)
        return block(escape_text(" ".join(element.text().split())))

    # --- Paragraph-level elements ----------------------------------------------------------

    def _hidden(self, paragraph: Element) -> bool:
        return any(
            child.tag == "text:hidden-paragraph" and child.get("text:is-hidden") == "true"
            for child in paragraph.elements()
        )

    def _paragraph(self, paragraph: Element) -> str:
        if self._hidden(paragraph):
            return ""
        style = paragraph.get("text:style-name")
        role = self.styles.role(style)
        if role in {Role.TITLE, Role.SUBTITLE}:
            text = self.inline(paragraph, TextProps())
            if not text:
                return ""
            return block(f"{MARK}# {text}" if role is Role.TITLE else f"{MARK}*{text}*")
        alone = _sole_formula(paragraph)
        if alone is not None:  # a formula alone in its paragraph is display math
            return block(self._formula_markdown(alone, display=True))
        text = self.inline(paragraph, self.styles.paragraph_props(style))
        return block(text) if text else ""

    def _heading(self, heading: Element) -> str:
        text = self.inline(heading, TextProps())  # a heading's own bold is not emphasis
        if not text:
            return ""
        level = heading.get("text:outline-level")
        number = int(level) if level.isdigit() else self._top
        hashes = "#" * min(6, 2 + max(0, number - self._top))
        return block(f"{MARK}{hashes} {text}")

    def _quote(self, paragraphs: list[Element]) -> str:
        lines = []
        for paragraph in paragraphs:
            text = self.inline(paragraph, TextProps())
            lines.append(f"{MARK}> {text}" if text else f"{MARK}>")
        return block("\n".join(lines))

    def _code(self, paragraphs: list[Element]) -> str:
        code = "\n".join(self.plain(paragraph) for paragraph in paragraphs).strip("\n")
        fence = fence_for(code)
        return block(f"{MARK}{fence}\n{code}\n{MARK}{fence}")

    def _list(self, element: Element, level: int, inherited: str) -> str:
        # A nested list without a style of its own uses its enclosing list's, one level down.
        style = element.get("text:style-name") or inherited
        items = [
            child
            for child in element.elements()
            if child.tag in {"text:list-item", "text:list-header"}
        ]
        if not style and items:
            first = next(items[0].elements(), None)
            style = (
                self.styles.list_style_of_paragraph(first.get("text:style-name")) if first else ""
            )
        kind = self.styles.list_level(style, level)
        number = kind.start
        lines = []
        for item in items:
            children = list(item.elements())
            if children and children[0].tag == "text:h":  # an outline-numbered heading
                lines.append(self.blocks(children).strip("\n"))
                continue
            start = item.get("text:start-value")
            if start.isdigit():
                number = int(start)
            content = self._item(children, level, style)
            if item.tag == "text:list-header":
                lines.append(content)
                continue
            marker = f"{number}. " if kind.numbered else "- "
            number += 1
            lines.append(MARK + marker + indent(content, len(marker)))
        return "\n".join(line for line in lines if line)

    def _item(self, children: list[Element], level: int, style: str) -> str:
        parts = []
        for child in children:
            if child.tag == "text:list":
                parts.append(self._list(child, level + 1, style))
            else:
                parts.append(self._block(child).strip("\n"))
        text = "\n".join(part for part in parts if part)
        tight = outside_code(text, lambda part: re.sub(r"\n[ \t]*\n+", "\n", part))
        return neutralize(tight, keep_marks=True)

    def _spend(self, size: int) -> bool:
        """Charge ``size`` characters to the document's growth budget; ``False`` past it."""
        if size > self._room:
            self._room = 0
            return False
        self._room -= size
        return True

    def _table(self, table: Element) -> str:
        found = table_to_markdown(table, self._cell, self._spend)
        if found.simplified:
            self.counts.tables_simplified += 1
        return block(found.markdown) if found.markdown else ""

    def _cell(self, cell: Element) -> str:
        texts = [self.inline(p, TextProps()) for p in _own_paragraphs(cell)]
        return " ".join(text.replace(LINE_BREAK, " ") for text in texts if text)

    # --- Inline ------------------------------------------------------------------------------

    def plain(self, paragraph: Element) -> str:
        """A code paragraph's text as written: no escaping, spaces and tabs kept."""
        out = []
        for piece in self._pieces(paragraph, TextProps()):
            if isinstance(piece, _Text):
                out.append(piece.text if piece.literal else _WHITESPACE.sub(" ", piece.text))
            elif piece.markdown == LINE_BREAK:
                out.append("\n")
        return "".join(out)

    def inline(self, paragraph: Element, props: TextProps) -> str:
        return self._write(self._normalize(self._pieces(paragraph, props)))

    def _pieces(self, element: Element, props: TextProps) -> list[_Piece]:
        pieces: list[_Piece] = []
        # Each level: its children, the properties, the link, and whether it is inside an unknown
        # element (only the outermost unknown element is listed in the note).
        stack: list[tuple[Any, TextProps, str | None, bool]] = [
            (iter(element.children), props, None, False)
        ]
        while stack:
            items, current, link, unknown = stack[-1]
            item = next(items, None)
            if item is None:
                stack.pop()
                continue
            if isinstance(item, str):
                pieces.append(_Text(item, current, link))
                continue
            tag = item.tag
            if tag in SPAN_LIKE:
                inner = self.styles.text_props(item.get("text:style-name"), current)
                if not inner.hidden:
                    stack.append((iter(item.children), inner, link, unknown))
            elif tag == "text:a":
                stack.append(
                    (iter(item.children), current, link or item.get("xlink:href"), unknown)
                )
            elif tag == "text:s":
                count = item.get("text:c")
                spaces = min(int(count), MAX_SPACES) if count.isdigit() else 1
                pieces.append(_Text(" " * spaces, current, link, literal=True))
            elif tag == "text:tab":
                pieces.append(_Text("\t", current, link, literal=True))
            elif tag == "text:line-break":
                pieces.append(_Raw(LINE_BREAK))
            elif tag == "text:note":
                pieces.append(_Raw(self._note(item)))
            elif tag == "office:annotation":
                self.counts.comments += 1
            elif tag == "text:hidden-text":
                if item.get("text:is-hidden") != "true":
                    pieces.append(_Text(item.get("text:string-value"), current, link))
            elif tag == "draw:frame":
                pieces.append(_Raw(self._frame(item)))
            elif tag == "draw:a":  # a linked frame: the frame matters, its link never does
                stack.append((iter(item.children), current, link, unknown))
            elif tag in DROPPED_INLINE:
                continue
            elif tag in FIELDS:
                stack.append((iter(item.children), current, link, unknown))
            else:
                if not unknown:
                    self._unknown(tag)
                stack.append((iter(item.children), current, link, True))  # its text is kept
        return pieces

    def _frame(self, frame: Element) -> str:
        """An image as a placeholder, a formula as LaTeX, a text box as its text."""
        formula = frame.find("draw:object")
        if formula is not None:  # its draw:image is LibreOffice's replacement picture
            return self._formula_markdown(formula, display=False)
        if frame.find("draw:image") is not None:
            self.counts.images += 1
            title = frame.find("svg:title")
            description = frame.find("svg:desc")
            label = next(
                (
                    " ".join(text.split())
                    for text in (
                        title.text() if title is not None else "",
                        description.text() if description is not None else "",
                        frame.get("draw:name"),
                    )
                    if text.strip()
                ),
                "",
            )
            shown = f"{self._image_word}: {label}" if label else self._image_word
            return f"*{escape_text(shown)}*"
        box = frame.find("draw:text-box")
        if box is not None:
            texts = [
                self.inline(p, TextProps()) for p in box.elements() if p.tag in {"text:p", "text:h"}
            ]
            return " ".join(text for text in texts if text)
        self._unknown(frame.tag)
        return escape_text(" ".join(frame.text().split()))

    def _formula_markdown(self, formula: Element, *, display: bool) -> str:
        found = self._formula(formula) if self._formula is not None else FormulaResult(None)
        if found.latex is not None and not self._spend(len(found.latex)):
            found = FormulaResult(None, None)  # past the growth budget: no more copies
        if found.latex is None:
            self.counts.formulas_kept += 1
            return inline_code(found.source) if found.source else f"*{self._formula_word}*"
        latex = escape_math(found.latex)
        return display_math(latex) if display else f"${latex}$"

    def _note(self, note: Element) -> str:
        if len(self.footnotes) >= MAX_NOTES:
            self._unknown("text:note")
            return ""
        number = len(self.footnotes) + 1
        self.footnotes.append("")  # its number is taken before notes nested in it get theirs
        body = note.find("text:note-body")
        paragraphs = _own_paragraphs(body) if body is not None else []
        texts = [self.inline(p, TextProps()) for p in paragraphs]
        self.footnotes[number - 1] = " ".join(text for text in texts if text)
        return f"[^{number}]"

    def _normalize(self, pieces: list[_Piece]) -> list[_Piece]:
        """ODF whitespace: runs collapse to one space, none at the start or the end."""
        out: list[_Piece] = []
        for piece in pieces:
            if isinstance(piece, _Text) and not piece.literal:
                text = _WHITESPACE.sub(" ", piece.text)
                previous = out[-1] if out else None
                ends_in_space = (
                    previous is None
                    or (isinstance(previous, _Raw) and previous.markdown == LINE_BREAK)
                    or (isinstance(previous, _Text) and previous.text.endswith(" "))
                )
                if ends_in_space:
                    text = text.lstrip(" ")
                if not text:
                    continue
                piece = _Text(text, piece.props, piece.link)
            if out and isinstance(piece, _Text) and isinstance(out[-1], _Text):
                last = out[-1]
                if (last.props, last.link) == (piece.props, piece.link):
                    out[-1] = _Text(last.text + piece.text, last.props, last.link, literal=True)
                    continue
            out.append(piece)
        while out and isinstance(out[-1], _Text) and not out[-1].text.strip():
            out.pop()
        if out and isinstance(out[-1], _Text):
            out[-1] = _Text(out[-1].text.rstrip(" "), out[-1].props, out[-1].link, literal=True)
        return out

    def _write(self, pieces: list[_Piece]) -> str:
        parts: list[str] = []
        index = 0
        while index < len(pieces):
            piece = pieces[index]
            if isinstance(piece, _Text) and piece.link is not None:
                group = [piece]
                while (
                    index + 1 < len(pieces)
                    and isinstance(pieces[index + 1], _Text)
                    and pieces[index + 1].link == piece.link  # type: ignore[union-attr]
                ):
                    index += 1
                    group.append(pieces[index])  # type: ignore[arg-type]
                parts.append(self._link(piece.link, group))
            elif isinstance(piece, _Text):
                group = [piece]
                while (
                    index + 1 < len(pieces)
                    and isinstance(pieces[index + 1], _Text)
                    and pieces[index + 1].link is None  # type: ignore[union-attr]
                ):
                    index += 1
                    group.append(pieces[index])  # type: ignore[arg-type]
                parts.append(_styled(group))
            else:
                parts.append(piece.markdown)
            index += 1
        return join_pieces(parts)

    def _link(self, url: str, group: list[_Text]) -> str:
        text = _styled([_Text(g.text, g.props, None, g.literal) for g in group]).strip()
        url = url.strip()
        if not url:
            return text
        if not SAFE_LINK.match(url) or ENTITY.search(url):  # javascript: never becomes a link
            return f"{text} ({inline_code(url)})" if text else inline_code(url)
        return f"[{text or escape_text(url)}]({link_target(url)})"

    def _unknown(self, tag: str) -> None:
        if tag in self.counts.unknown or len(self.counts.unknown) < MAX_UNKNOWN:
            self.counts.unknown[tag] = None

    # --- Notes ----------------------------------------------------------------------------------

    def notes(self) -> tuple[ConversionNote, ...]:
        found: list[ConversionNote] = []
        if self.counts.images:
            count = NoteItem(str(self.counts.images))
            found.append(ConversionNote(NoteKind.IMAGES_NOT_EXTRACTED, (count,)))
        if self.counts.formulas_kept:
            count = NoteItem(str(self.counts.formulas_kept))
            found.append(ConversionNote(NoteKind.FORMULA_KEPT_AS_SOURCE, (count,)))
        if self.counts.unknown:
            items = tuple(NoteItem(tag) for tag in self.counts.unknown)
            found.append(ConversionNote(NoteKind.ELEMENTS_SIMPLIFIED, items))
        if self.counts.tables_simplified:
            count = NoteItem(str(self.counts.tables_simplified))
            found.append(ConversionNote(NoteKind.TABLE_SIMPLIFIED, (count,)))
        dropped = []
        if self.counts.comments:
            dropped.append(NoteItem(str(self.counts.comments), NoteReason.COMMENTS.value))
        if self.counts.changes:
            dropped.append(NoteItem(str(self.counts.changes), NoteReason.TRACKED_CHANGES.value))
        if dropped:
            found.append(ConversionNote(NoteKind.REVISIONS_DROPPED, tuple(dropped)))
        return tuple(found)


def _own_paragraphs(element: Element) -> list[Element]:
    """The paragraphs and headings of ``element``, never those nested in them or in notes (they
    are part of their parent's text): each one is written once, in one pass."""
    found: list[Element] = []
    pending = list(reversed(list(element.elements())))
    while pending:
        child = pending.pop()
        if child.tag in {"text:p", "text:h"}:
            found.append(child)
        elif child.tag != "text:note":
            pending.extend(reversed(list(child.elements())))
    return found


def _sole_formula(paragraph: Element) -> Element | None:
    """The formula object of a paragraph that holds nothing else (spaces aside)."""
    found: Element | None = None
    for child in paragraph.children:
        if isinstance(child, str):
            if child.strip():
                return None
            continue
        if child.tag in {"text:soft-page-break", "text:bookmark", "text:bookmark-start"}:
            continue
        formula = child.find("draw:object") if child.tag == "draw:frame" else None
        if formula is None or found is not None:
            return None
        found = formula
    return found


def display_math(latex: str) -> str:
    """``$$`` lines are ClearMD's; the math between them is never read as Markdown blocks."""
    lines = "\n".join(math_line(line) for line in latex.split("\n"))
    return f"{MARK}$$\n{lines}\n{MARK}$$"


def _split(text: str) -> tuple[str, str, str]:
    core = text.strip(" \t")
    if not core:
        return text, "", ""
    start = text.index(core)
    return text[:start], core, text[start + len(core) :]


def _styled(group: list[_Text]) -> str:
    """Runs of text with their delimiters opened and closed as the properties change."""
    out: list[str] = []
    opened: list[str] = []
    pending = ""
    for piece in group:
        lead, core, trail = _split(piece.text)
        if not core:
            pending += piece.text
            continue
        wanted = _active(piece.props)
        keep = 0
        while keep < len(opened) and opened[keep] in wanted:
            keep += 1
        out.extend(_closer(key) for key in reversed(opened[keep:]))
        opened = opened[:keep]
        out.append(pending + lead)
        pending = ""
        for key in wanted:
            if key not in opened:
                out.append(_opener(key))
                opened.append(key)
        out.append(inline_code(core) if piece.props.mono else escape_text(core))
        pending = trail
    out.extend(_closer(key) for key in reversed(opened))
    out.append(pending)
    # The same joining rules as between pieces: a backtick of the text never glues to a code span.
    return join_pieces(out)
