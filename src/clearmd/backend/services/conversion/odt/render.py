"""OpenDocument text → Markdown: the subset of spec 003, written through ``markdown_out``.

A paragraph is flattened into runs of text with their effective properties (paragraph style,
spans and their parents), equal neighbours merged, and written with delimiters that open and
close as the properties change (``**a*b***``), spaces kept outside them. Everything outside the
subset keeps its text and is listed in a note. Images become placeholders; formulas, LaTeX.

``OdtRenderer`` keeps the recursive entry points (``document``, ``blocks``, ``inline``); the
writers in ``odt/writer/`` are plain functions that take it, so a level of nesting costs the same
Python frames as when they were methods.
"""

from collections.abc import Callable

from clearmd.backend.schemas.notes import ConversionNote
from clearmd.backend.services.conversion.inline import TextProps
from clearmd.backend.services.conversion.markdown_out import MARK, block, neutralize, tidy
from clearmd.backend.services.conversion.odt.styles import Role, Styles
from clearmd.backend.services.conversion.odt.writer.dispatch import write_block
from clearmd.backend.services.conversion.odt.writer.inline import text_pieces
from clearmd.backend.services.conversion.odt.writer.leaf_blocks import code_block, quote_block
from clearmd.backend.services.conversion.odt.writer.paragraphs import role_of
from clearmd.backend.services.conversion.odt.writer.report import collect_notes
from clearmd.backend.services.conversion.odt.writer.state import FormulaHandler, OdtState
from clearmd.backend.services.conversion.xmltree import Element, int_attribute


class OdtRenderer:
    """Elements → Markdown. What a run accumulates lives in ``state``."""

    def __init__(
        self,
        styles: Styles,
        *,
        formula: FormulaHandler | None = None,
        language: str = "",
        source_size: int = 0,
        pictures: Callable[[str], str | None] | None = None,
    ) -> None:
        self.state = OdtState(
            styles,
            formula=formula,
            language=language,
            source_size=source_size,
            pictures=pictures,
        )

    # --- Entry points -------------------------------------------------------------------------

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
        self.state.top = min(levels, default=1)
        rendered = self.blocks(list(text.elements()))
        if self.state.footnotes:
            # A definition's text is block content to a footnote-aware viewer: neutralized first.
            notes = "\n".join(
                f"{MARK}[^{n}]: {neutralize(note)}"
                for n, note in enumerate(self.state.footnotes, start=1)
            )
            rendered += block(notes)
        return neutralize(tidy(rendered))

    def blocks(self, elements: list[Element]) -> str:
        parts: list[str] = []
        index = 0
        while index < len(elements):
            element = elements[index]
            role = role_of(self, element)
            if role in {Role.QUOTE, Role.CODE}:
                run = [element]
                while index + 1 < len(elements) and role_of(self, elements[index + 1]) is role:
                    index += 1
                    run.append(elements[index])
                parts.append(
                    quote_block(self, run) if role is Role.QUOTE else code_block(self, run)
                )
            else:
                parts.append(write_block(self, element))
            # Something written stands between this list and the next (a section passes through:
            # its own blocks decide).
            if element.tag not in {"text:list", "text:section"} and parts[-1].strip():
                self.state.last_list = None
            index += 1
        return "".join(parts)

    def inline(self, paragraph: Element, props: TextProps) -> str:
        """The Markdown of a paragraph's text with ``props`` as its base properties."""
        return self.state.writer.write(
            self.state.writer.normalize(text_pieces(self, paragraph, props))
        )

    def notes(self) -> tuple[ConversionNote, ...]:
        """The notes this run earned."""
        return collect_notes(self)
