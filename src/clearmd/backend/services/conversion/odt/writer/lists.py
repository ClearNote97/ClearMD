"""Lists: numbering and nesting of ``text:list``, each level indented within the budget."""

from clearmd.backend.services.conversion.markdown_out import (
    MARK,
    indent,
    indent_all,
    neutralize,
    own_line,
    starts_tight,
    starts_with_fence,
)
from clearmd.backend.services.conversion.odt.writer.paragraphs import own_paragraphs
from clearmd.backend.services.conversion.odt.writer.state import Writer
from clearmd.backend.services.conversion.odt.writer.vocab import MAX_LIST_LEVEL
from clearmd.backend.services.conversion.xmltree import Element, int_attribute


def continues_numbering(element: Element) -> bool:
    return element.get("text:continue-numbering") == "true" or bool(
        element.get("text:continue-list")
    )


def list_block(w: Writer, element: Element, level: int, inherited: str) -> str:
    # A nested list without a style of its own uses its enclosing list's, one level down.
    style = element.get("text:style-name") or inherited
    items = [
        child for child in element.elements() if child.tag in {"text:list-item", "text:list-header"}
    ]
    if not style and items:
        first = next(items[0].elements(), None)
        style = (
            w.state.styles.list_style_of_paragraph(first.get("text:style-name")) if first else ""
        )
    kind = w.state.styles.list_level(style, level)
    continues = continues_numbering(element)
    number = w.state.numbers.get((style, level), kind.start - 1) + 1 if continues else kind.start
    # Two lists of the same kind one after the other would be one list to Markdown (a restart
    # lost): the second uses the other markers ("1)" for "1.", "*" for "-").
    previous = w.state.last_list
    alternate = previous == (kind.numbered, False) and not continues
    delimiter = ")" if alternate else "."
    bullet = "* " if alternate else "- "
    lines: list[str] = []
    width = 0  # the marker width of the last item: a skipped level nests in it
    written: tuple[bool, bool] | None = None  # the markers of the last line at this level
    for item in items:
        children = list(item.elements())
        if children and children[0].tag == "text:h":  # an outline-numbered heading
            lines.append(w.blocks(children).strip("\n"))
            continue
        number = int_attribute(item.get("text:start-value"), number)
        content = list_item(w, children, level, style)
        if not content:
            continue
        if item.tag == "text:list-header":  # no marker, its own block
            lines.append("\n" + content + "\n")
            width = 0
            continue
        if all(child.tag == "text:list" for child in children):
            # A skipped level is one nesting step: inside the item before, or at this level.
            if width:
                separator = "\n" if starts_tight(content) else "\n\n"
                lines[-1] += separator + indented(w, content, width)
            else:
                lines.append(content)
                written = w.state.last_list  # its markers are the ones at this level now
            continue
        marker = f"{number}{delimiter} " if kind.numbered else bullet
        number += 1
        width = len(marker)
        written = (kind.numbered, alternate)
        if starts_with_fence(content):  # the marker alone, the fence below it
            lines.append(MARK + marker.rstrip() + "\n" + indented(w, content, width))
        else:
            lines.append(MARK + marker + indented(w, content, width, first=False))
    if kind.numbered:
        w.state.numbers[(style, level)] = number - 1
    w.state.last_list = written
    return "\n".join(line for line in lines if line).strip("\n")


def list_item(w: Writer, children: list[Element], level: int, style: str) -> str:
    """An item's content: paragraphs (with their roles), nested lists and the rest. A nested
    list that starts at 1 or a bullet list follows its paragraph directly; anything else is
    separated by a blank line, so it never merges into the paragraph before it."""
    parts: list[str] = []
    group: list[Element] = []
    w.state.last_list = None  # sibling lists inside the item alternate too

    def flush() -> None:
        if group:
            parts.append(w.blocks(list(group)).strip("\n"))
            group.clear()
            w.state.last_list = None

    for child in children:
        if child.tag == "text:list" and level >= MAX_LIST_LEVEL:
            w.state.note_unknown("text:list")  # deeper than any editor writes: its paragraphs here
            group.extend(own_paragraphs(w, child))
        elif child.tag == "text:list":
            flush()
            parts.append(list_block(w, child, level + 1, style))
        else:
            group.append(child)
    flush()
    joined: list[str] = []
    for part in (p for p in parts if p):
        if joined:
            joined.append("\n" if starts_tight(part) else "\n\n")
        joined.append(part)
    text = "".join(joined)
    # Neutralized here, at the item's own column, then marked as ClearMD's: the enclosing
    # levels only indent it, and never read its indented lines again as document text (a
    # second pass would take a paragraph indented 4 columns after a blank for code).
    return "\n".join(own_line(line) for line in neutralize(text, keep_marks=True).split("\n"))


def indented(w: Writer, content: str, width: int, *, first: bool = True) -> str:
    """``content`` indented by ``width`` (from its second line when not ``first``), the
    indentation charged to the budget; past it, the lines stay where they are (each one is
    ClearMD's, already neutralized: text kept, nesting lost)."""
    lines = content.count("\n") + (1 if first else 0)
    if not w.state.spend(width * lines):
        w.state.note_unknown("text:list")
        return content
    return indent_all(content, width) if first else indent(content, width)
