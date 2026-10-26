"""OpenDocument text → Markdown: the subset of spec 003, written through ``markdown_out``.

A paragraph is flattened into runs of text with their effective properties (paragraph style,
spans and their parents), equal neighbours merged, and written with delimiters that open and
close as the properties change (``**a*b***``), spaces kept outside them. Everything outside the
subset keeps its text and is listed in a note. Images become placeholders; formulas, LaTeX.
"""

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field, replace
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
    tidy,
)
from clearmd.backend.services.conversion.odt.styles import Role, Styles, TextProps
from clearmd.backend.services.conversion.odt.tables import table_to_markdown
from clearmd.backend.services.conversion.odt.xmltree import Element, int_attribute

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
MAX_LIST_LEVEL = 10  # LibreOffice's deepest; deeper lists are flattened into the tenth level
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


# A formula object → its LaTeX (without $), or ``None`` with the source to show instead
# (StarMath, or nothing) when it is not converted; ``formula`` is false for a chart or another
# embedded object, which is shown as an image placeholder.
FormulaHandler = Callable[[Element], "FormulaResult"]


@dataclass(frozen=True)
class FormulaResult:
    latex: str | None
    source: str | None = None
    formula: bool = True


@dataclass
class _Counts:
    images: int = 0
    formulas_kept: int = 0
    comments: int = 0
    changes: int = 0
    tables_simplified: int = 0
    formatting_dropped: int = 0
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
        self._numbers: dict[tuple[str, int], int] = {}  # last number of each list style and level
        # The last top-level list written, if nothing came after it: (numbered, other markers).
        self._last_list: tuple[bool, bool] | None = None

    # --- Document -------------------------------------------------------------------------

    def document(self, content: Element) -> str:
        body = content.find("office:body")
        text = body.find("office:text") if body is not None else None
        if text is None:
            return ""
        # Headings that are really shown: not deleted (tracked changes), not in notes or hidden.
        skipped = {"text:tracked-changes", "text:note", "office:annotation"}
        levels = []
        pending = list(text.elements())
        while pending:
            element = pending.pop()
            if element.tag in skipped or element.get("text:display") == "none":
                continue
            if element.tag == "text:h":
                levels.append(int_attribute(element.get("text:outline-level"), 1, cap=10))
            pending.extend(element.elements())
        self._top = min(levels, default=1)
        rendered = self.blocks(list(text.elements()))
        if self.footnotes:
            # A definition's text is block content to a footnote-aware viewer: neutralized first.
            notes = "\n".join(
                f"{MARK}[^{n}]: {neutralize(note)}"
                for n, note in enumerate(self.footnotes, start=1)
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
            # Something written stands between this list and the next (a section passes through:
            # its own blocks decide).
            if element.tag not in {"text:list", "text:section"} and parts[-1].strip():
                self._last_list = None
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
        if tag in {"draw:frame", "draw:a"}:  # a page-anchored frame sits directly in the text
            frames = [element] if tag == "draw:frame" else list(element.elements("draw:frame"))
            return block(" ".join(self._frame(frame) for frame in frames))
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
        """Hidden by a field in it, or by its style (``text:display="none"``)."""
        if self.styles.paragraph_props(paragraph.get("text:style-name")).hidden:
            return True
        return any(
            child.tag == "text:hidden-paragraph" and child.get("text:is-hidden") == "true"
            for child in paragraph.elements()
        )

    def _props(self, paragraph: Element) -> TextProps:
        return self.styles.paragraph_props(paragraph.get("text:style-name"))

    def _paragraph(self, paragraph: Element) -> str:
        if self._hidden(paragraph):
            return ""
        style = paragraph.get("text:style-name")
        role = self.styles.role(style)
        if role in {Role.TITLE, Role.SUBTITLE}:
            text = self.inline(paragraph, TextProps()).replace(LINE_BREAK, " ")
            if not text:
                return ""
            return block(f"{MARK}# {text}" if role is Role.TITLE else f"{MARK}*{text}*")
        alone = _sole_formula(paragraph)
        if alone is not None:  # a formula alone in its paragraph is display math
            shown = self._formula_markdown(alone, display=True)
            if shown is not None:
                return block(shown)
        text = self.inline(paragraph, self._props(paragraph))
        return block(text) if text else ""

    def _heading(self, heading: Element) -> str:
        if self._hidden(heading):
            return ""
        # A heading's own bold is not emphasis; a line break in it never ends the heading.
        text = self.inline(heading, TextProps()).replace(LINE_BREAK, " ")
        if not text:
            return ""
        number = int_attribute(heading.get("text:outline-level"), self._top, cap=10)
        hashes = "#" * min(6, 2 + max(0, number - self._top))
        return block(f"{MARK}{hashes} {text}")

    def _quote(self, paragraphs: list[Element]) -> str:
        lines = []
        for paragraph in paragraphs:
            if self._hidden(paragraph):
                continue
            text = self.inline(paragraph, self._props(paragraph))
            lines.append(f"{MARK}> {text}" if text else f"{MARK}>")
        if not lines:
            return ""
        return block("\n".join(lines))

    def _code(self, paragraphs: list[Element]) -> str:
        shown = [paragraph for paragraph in paragraphs if not self._hidden(paragraph)]
        if not shown:
            return ""
        code = "\n".join(self.plain(paragraph) for paragraph in shown).strip("\n")
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
        continues = _continues(element)
        number = self._numbers.get((style, level), kind.start - 1) + 1 if continues else kind.start
        # Two lists of the same kind one after the other would be one list to Markdown (a restart
        # lost): the second uses the other markers ("1)" for "1.", "*" for "-").
        previous = self._last_list
        alternate = previous == (kind.numbered, False) and not continues
        delimiter = ")" if alternate else "."
        bullet = "* " if alternate else "- "
        lines: list[str] = []
        width = 0  # the marker width of the last item: a skipped level nests in it
        written: tuple[bool, bool] | None = None  # the markers of the last line at this level
        for item in items:
            children = list(item.elements())
            if children and children[0].tag == "text:h":  # an outline-numbered heading
                lines.append(self.blocks(children).strip("\n"))
                continue
            number = int_attribute(item.get("text:start-value"), number)
            content = self._item(children, level, style)
            if not content:
                continue
            if item.tag == "text:list-header":  # no marker, its own block
                lines.append("\n" + content + "\n")
                width = 0
                continue
            if all(child.tag == "text:list" for child in children):
                # A skipped level is one nesting step: inside the item before, or at this level.
                if width:
                    separator = "\n" if _starts_tight(content) else "\n\n"
                    lines[-1] += separator + self._indented(content, width)
                else:
                    lines.append(content)
                    written = self._last_list  # its markers are the ones at this level now
                continue
            marker = f"{number}{delimiter} " if kind.numbered else bullet
            number += 1
            width = len(marker)
            written = (kind.numbered, alternate)
            lines.append(MARK + marker + self._indented(content, width, first=False))
        if kind.numbered:
            self._numbers[(style, level)] = number - 1
        self._last_list = written
        return "\n".join(line for line in lines if line).strip("\n")

    def _item(self, children: list[Element], level: int, style: str) -> str:
        """An item's content: paragraphs (with their roles), nested lists and the rest. A nested
        list that starts at 1 or a bullet list follows its paragraph directly; anything else is
        separated by a blank line, so it never merges into the paragraph before it."""
        parts: list[str] = []
        group: list[Element] = []
        self._last_list = None  # sibling lists inside the item alternate too

        def flush() -> None:
            if group:
                parts.append(self.blocks(list(group)).strip("\n"))
                group.clear()
                self._last_list = None

        for child in children:
            if child.tag == "text:list" and level >= MAX_LIST_LEVEL:
                self._unknown("text:list")  # deeper than any editor writes: its paragraphs here
                group.extend(self._own_paragraphs(child))
            elif child.tag == "text:list":
                flush()
                parts.append(self._list(child, level + 1, style))
            else:
                group.append(child)
        flush()
        text = ""
        for part in (p for p in parts if p):
            if not text:
                text = part
                continue
            text += ("\n" if _starts_tight(part) else "\n\n") + part
        # Neutralized here, at the item's own column, then marked as ClearMD's: the enclosing
        # levels only indent it, and never read its indented lines again as document text (a
        # second pass would take a paragraph indented 4 columns after a blank for code).
        return "\n".join(_own_line(line) for line in neutralize(text, keep_marks=True).split("\n"))

    def _indented(self, content: str, width: int, *, first: bool = True) -> str:
        """``content`` indented by ``width`` (from its second line when not ``first``), the
        indentation charged to the budget; past it, the lines stay where they are (each one is
        ClearMD's, already neutralized: text kept, nesting lost)."""
        lines = content.count("\n") + (1 if first else 0)
        if not self._spend(width * lines):
            self._unknown("text:list")
            return content
        return _indent_all(content, width) if first else indent(content, width)

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
        shown = [p for p in self._own_paragraphs(cell) if not self._hidden(p)]
        texts = [self.inline(p, self._props(p)) for p in shown]
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
            elif piece.markdown.startswith("[^"):  # a note's reference, as written in the code
                out.append(piece.markdown)
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
                spaces = int_attribute(item.get("text:c"), 1, cap=MAX_SPACES)
                if spaces > 1 and not self._spend(spaces):  # one element, many characters
                    spaces = 1
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
                shown = self._frame(item)
                if shown:  # nothing to show (an empty formula): no piece between two spaces
                    pieces.append(_Raw(shown))
            elif tag == "draw:a":  # a linked frame: the frame matters, its link never does
                stack.append((iter(item.children), current, link, unknown))
            elif tag in DROPPED_INLINE:
                continue
            elif tag in FIELDS:
                if item.get("text:display") != "none":
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
            shown = self._formula_markdown(formula, display=False)
            if shown is not None:
                return shown
            # Not a formula (a chart, another embedded object): a placeholder, like an image.
        if formula is not None or frame.find("draw:image") is not None:
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
        if box is not None:  # its lists and tables too; never glued to the text around it
            visible = [p for p in self._own_paragraphs(box) if not self._hidden(p)]
            texts = [self.inline(p, self._props(p)).replace(LINE_BREAK, " ") for p in visible]
            joined = " ".join(text for text in texts if text)
            return f" {joined} " if joined else ""
        self._unknown(frame.tag)
        return escape_text(" ".join(frame.text().split()))

    def _formula_markdown(self, formula: Element, *, display: bool) -> str | None:
        """The formula's Markdown; ``None`` when the object is not a formula at all."""
        found = self._formula(formula) if self._formula is not None else FormulaResult(None)
        if not found.formula:
            return None
        if found.latex is not None and not found.latex.strip():
            return ""  # an empty formula: nothing to show, never a stray "$$"
        if found.latex is not None and not self._spend(len(found.latex)):
            found = FormulaResult(None, found.source)  # past the growth budget
        if found.latex is None:
            self.counts.formulas_kept += 1
            if found.source and self._spend(len(found.source)):  # the source is charged too
                return inline_code(found.source)
            return f"*{self._formula_word}*"
        latex = escape_math(found.latex)
        return display_math(latex) if display else f"${latex}$"

    def _note(self, note: Element) -> str:
        if len(self.footnotes) >= MAX_NOTES:
            self._unknown("text:note")
            return ""
        number = len(self.footnotes) + 1
        self.footnotes.append("")  # its number is taken before notes nested in it get theirs
        body = note.find("text:note-body")
        paragraphs = self._own_paragraphs(body) if body is not None else []
        shown = [p for p in paragraphs if not self._hidden(p)]
        texts = [self.inline(p, self._props(p)).replace(LINE_BREAK, " ") for p in shown]
        # An empty definition would not be one: the reference would show as text.
        self.footnotes[number - 1] = " ".join(text for text in texts if text) or "…"
        return f"[^{number}]"

    def _normalize(self, pieces: list[_Piece]) -> list[_Piece]:
        """ODF whitespace: runs collapse to one space, none at the start or the end; equal
        neighbours are merged (their texts joined once: linear)."""
        cleaned: list[_Piece] = []
        for piece in pieces:
            if isinstance(piece, _Text) and not piece.literal:
                text = _WHITESPACE.sub(" ", piece.text)
                previous = cleaned[-1] if cleaned else None
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
            cleaned.append(piece)
        out: list[_Piece] = []
        merged: list[str] = []  # the texts that make out[-1], joined when the run ends

        def close() -> None:
            last = out[-1] if out else None
            if merged and isinstance(last, _Text):
                out[-1] = _Text("".join(merged), last.props, last.link, literal=True)
            merged.clear()

        for piece in cleaned:
            last = out[-1] if out else None
            if (
                isinstance(piece, _Text)
                and isinstance(last, _Text)
                and (last.props, last.link) == (piece.props, piece.link)
            ):
                if not merged:
                    merged.append(last.text)
                merged.append(piece.text)
                continue
            close()
            out.append(piece)
        close()
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
                parts.append(self._style(group))
            else:
                parts.append(piece.markdown)
            index += 1
        return join_pieces(parts)

    def _style(self, group: list[_Text]) -> str:
        safe, dropped = _safe_emphasis(group)
        written = _styled(safe)
        if _unpaired_delimiters(written):  # the pairing itself fails (CommonMark's rule of 3…)
            plain = [
                _Text(p.text, _without(p.props, set(_EMPHASIS)), p.link, p.literal) for p in safe
            ]
            dropped += sum(
                1 for old, new in zip(safe, plain, strict=True) if old.props != new.props
            )
            written = _styled(plain)
        self.counts.formatting_dropped += dropped
        return written

    def _link(self, url: str, group: list[_Text]) -> str:
        written = self._style([_Text(g.text, g.props, None, g.literal) for g in group])
        lead, text, trail = _split(written)  # the spaces around the text stay outside the link
        url = url.strip()
        # Each piece of a link repeats its address: charged, and past the budget only the text.
        if not url or not self._spend(len(url)):
            return written
        if not SAFE_LINK.match(url) or ENTITY.search(url):  # javascript: never becomes a link
            shown = f"{text} ({inline_code(url)})" if text else inline_code(url)
        else:
            shown = f"[{text or escape_text(url)}]({link_target(url)})"
        return lead + shown + trail

    def _own_paragraphs(self, element: Element) -> list[Element]:
        """The paragraphs and headings of ``element``, never those nested in them or in notes
        (they are part of their parent's text), each written once, in one pass; hidden sections,
        comments, deletions and generated content are left out, as ``_block`` does."""
        found: list[Element] = []
        pending = list(reversed(list(element.elements())))
        while pending:
            child = pending.pop()
            tag = child.tag
            if tag in {"text:p", "text:h"}:
                found.append(child)
            elif tag == "text:tracked-changes":
                self.counts.changes += sum(1 for _ in child.elements("text:changed-region"))
            elif tag == "office:annotation":
                self.counts.comments += 1
            elif tag == "text:section" and child.get("text:display") == "none":
                continue
            elif tag not in DROPPED_BLOCKS and tag != "text:note":
                pending.extend(reversed(list(child.elements())))
        return found

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
        if self.counts.formatting_dropped:
            count = NoteItem(str(self.counts.formatting_dropped))
            found.append(ConversionNote(NoteKind.FORMATTING_DROPPED, (count,)))
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


def _continues(element: Element) -> bool:
    return element.get("text:continue-numbering") == "true" or bool(
        element.get("text:continue-list")
    )


def _starts_tight(part: str) -> bool:
    """A nested list Markdown lets follow a paragraph directly: bullets, or numbers from 1."""
    return re.match(rf"{MARK}(?:[-*] |1[.)] )", part) is not None


def _own_line(line: str) -> str:
    """``line`` marked as ClearMD's, after its indentation (where ``outside_code`` looks)."""
    content = line.lstrip(" \t")
    if not content or content.startswith(MARK):
        return line
    return line[: len(line) - len(content)] + MARK + content


def _indent_all(text: str, width: int) -> str:
    return "\n".join(" " * width + line if line else "" for line in text.split("\n"))


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
    pending: list[str] = []  # spaces between two runs, joined once
    for piece in group:
        lead, core, trail = _split(piece.text)
        if not core:
            pending.append(piece.text)
            continue
        wanted = _active(piece.props)
        keep = 0
        while keep < len(opened) and opened[keep] in wanted:
            keep += 1
        out.extend(_closer(key) for key in reversed(opened[keep:]))
        opened = opened[:keep]
        out.append("".join(pending) + lead)
        pending.clear()
        for key in wanted:
            if key not in opened:
                out.append(_opener(key))
                opened.append(key)
        out.append(inline_code(core) if piece.props.mono else escape_text(core))
        pending.append(trail)
    out.extend(_closer(key) for key in reversed(opened))
    out.append("".join(pending))
    # The same joining rules as between pieces: a backtick of the text never glues to a code span.
    return join_pieces(out)


# --- Emphasis Markdown can hold -------------------------------------------------------------

_EMPHASIS = ("bold", "italic", "strike")


def _kind(char: str) -> str:
    """CommonMark's classes for the characters around a delimiter run."""
    if char.isspace():
        return "space"
    return "punctuation" if unicodedata.category(char)[0] in "PS" else "word"


def _without(props: TextProps, keys: set[str]) -> TextProps:
    return replace(
        props,
        bold=props.bold and "bold" not in keys,
        italic=props.italic and "italic" not in keys,
        strike=props.strike and "strike" not in keys,
    )


def _flanking(before: str, after: str, *, left: bool) -> bool:
    """CommonMark's left- (``left``) or right-flanking delimiter run."""
    near, far = (_kind(after), _kind(before)) if left else (_kind(before), _kind(after))
    return near != "space" and (near != "punctuation" or far != "word")


def _runs(
    tokens: list[tuple[str, str, bool]], before: str, after: str
) -> tuple[set[str], set[str]]:
    """The keys whose delimiters at one boundary would show literally: (closing, opening). The
    boundary's text is ``before``, the closers and openers ``tokens``, then ``after``; each
    maximal run of the same delimiter character is judged by its real neighbours."""
    chars = [before, *(text for text, _, _ in tokens), after]
    closing: set[str] = set()
    opening: set[str] = set()
    position = 0
    while position < len(tokens):
        text, key, _ = tokens[position]
        end = position
        if key in _EMPHASIS:
            while (
                end + 1 < len(tokens)
                and tokens[end + 1][1] in _EMPHASIS
                and tokens[end + 1][0][0] == text[0]
            ):
                end += 1
            run = tokens[position : end + 1]
            left, right = chars[position][-1], chars[end + 2][0]
            if any(not opens for *_, opens in run) and not _flanking(left, right, left=False):
                closing.update(key for _, key, opens in run if not opens)
            if any(opens for *_, opens in run) and not _flanking(left, right, left=True):
                opening.update(key for _, key, opens in run if opens)
        position = end + 1
    return closing, opening


MAX_EMPHASIS_PASSES = 8


def _safe_emphasis(group: list[_Text]) -> tuple[list[_Text], int]:
    """The group with the emphasis Markdown would show as literal ``*`` or ``~`` left out, and
    how many runs lost a style. Each pass replays ``_styled`` (the same stack of open styles) and
    judges every delimiter run between two touching runs of text by the characters actually
    written around it: the text, ClearMD's own ``<u>`` or ``<sup>`` tags, other delimiters
    (``word**"quoted"**s`` and ``**<u>a</u>**b`` show their asterisks). A failing style is
    dropped from the run next to it, and the pass is repeated; after a few passes the group
    loses its emphasis (plain text is always safe). Each pass is linear."""
    split = [_split(piece.text) for piece in group]
    cores = [index for index, (_, core, _) in enumerate(split) if core]
    if len(cores) < 2:
        return group, 0
    written = [
        inline_code(split[i][1]) if group[i].props.mono else escape_text(split[i][1]) for i in cores
    ]
    touching = [False] + [
        not (split[cores[k - 1]][2] or split[cores[k]][0])
        and all(not group[i].text for i in range(cores[k - 1] + 1, cores[k]))
        for k in range(1, len(cores))
    ]
    props = [group[i].props for i in cores]
    dropped = 0
    for _ in range(MAX_EMPHASIS_PASSES):
        failing: dict[int, set[str]] = {}
        opened: list[str] = []
        for k in range(len(cores)):
            wanted = _active(props[k])
            keep = 0
            while keep < len(opened) and opened[keep] in wanted:
                keep += 1
            tokens = [(_closer(key), key, False) for key in reversed(opened[keep:])]
            opened = opened[:keep]
            for key in wanted:
                if key not in opened:
                    tokens.append((_opener(key), key, True))
                    opened.append(key)
            if k and touching[k] and tokens:
                closing, opening = _runs(tokens, written[k - 1][-1], written[k][0])
                if closing:
                    failing.setdefault(k - 1, set()).update(closing)
                if opening:
                    failing.setdefault(k, set()).update(opening)
        if not failing:
            break
        for k, keys in failing.items():
            props[k] = _without(props[k], keys)
            dropped += 1
    else:  # still failing: no emphasis at all in this group
        for k, value in enumerate(props):
            if any(getattr(value, key) for key in _EMPHASIS):
                props[k] = _without(value, set(_EMPHASIS))
                dropped += 1
    if not dropped:
        return group, 0
    safe = list(group)
    for k, index in enumerate(cores):
        piece = group[index]
        safe[index] = _Text(piece.text, props[k], piece.link, piece.literal)
    return safe, dropped


_ASCII_PUNCTUATION = frozenset("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")


def _code_span_end(text: str, start: int, end: int) -> int:
    """Where the code span opened by the backtick run ``text[start:end]`` ends: after the next run
    of the same length, or at ``end`` when there is none (the backticks are then text)."""
    length = end - start
    position = end
    while position < len(text):
        if text[position] != "`":
            position += 1
            continue
        run_end = position
        while run_end < len(text) and text[run_end] == "`":
            run_end += 1
        if run_end - position == length:
            return run_end
        position = run_end
    return end


def _unpaired_delimiters(text: str) -> bool:
    """Whether a viewer would show one of ClearMD's own ``*`` or ``~`` literally in ``text`` (a
    run of inline text as ``_styled`` writes it: the document's own ``*`` and ``~`` are escaped).

    CommonMark's emphasis algorithm (spec 0.31, "process emphasis"), in the standard library:
    delimiter runs with their flanking, the rule of three, openers bottom per kind; GFM's
    strike-through pairs runs of exactly two tildes. Code spans and escapes are skipped."""
    runs: list[list[Any]] = []  # [character, count, can_open, can_close, original count]
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text) and text[index + 1] in _ASCII_PUNCTUATION:
            index += 2
            continue
        if char == "`":
            end = index
            while end < len(text) and text[end] == "`":
                end += 1
            index = _code_span_end(text, index, end)
            continue
        if char in "*~":
            end = index
            while end < len(text) and text[end] == char:
                end += 1
            before = text[index - 1] if index else " "
            after = text[end] if end < len(text) else " "
            opens = _flanking(before, after, left=True)
            closes = _flanking(before, after, left=False)
            if char == "~" and end - index != 2:
                return True  # GFM: one tilde is text, three or more are not strike-through
            runs.append([char, end - index, opens, closes, end - index])
            index = end
            continue
        index += 1
    # The openers still unpaired, in order, with a sequence number; a closer pairs with the
    # nearest compatible one. One further down would leave the ones above it unpaired (shown as
    # written): the answer is already known. ``bottom`` keeps failed searches from rescanning.
    stack: list[tuple[int, list[Any]]] = []
    bottom: dict[tuple[str, bool, int], int] = {}
    for sequence, run in enumerate(runs):
        char, _, opens, closes, original = run
        key = (char, opens, original % 3)
        while closes and run[1]:
            found = -1
            position = len(stack) - 1
            while position >= 0 and stack[position][0] >= bottom.get(key, 0):
                candidate = stack[position][1]
                if candidate[0] == char and _pairs(candidate, run):
                    found = position
                    break
                position -= 1
            if found == -1:
                bottom[key] = sequence
                break
            if found != len(stack) - 1:
                return True
            opener = stack[-1][1]
            use = 2 if run[1] >= 2 and opener[1] >= 2 else 1
            opener[1] -= use
            run[1] -= use
            if not opener[1]:
                stack.pop()
        if run[1]:
            if not opens:
                return True  # a closer left over that cannot open
            stack.append((sequence, run))
    return bool(stack)


def _pairs(opener: list[Any], closer: list[Any]) -> bool:
    """CommonMark's rule of three for ``*``; GFM strike-through pairs equal runs of ``~``."""
    if opener[0] == "~":
        return bool(opener[1] == closer[1])
    both = opener[3] or closer[2]
    total = opener[4] + closer[4]
    return not (both and total % 3 == 0 and not (opener[4] % 3 == 0 and closer[4] % 3 == 0))
