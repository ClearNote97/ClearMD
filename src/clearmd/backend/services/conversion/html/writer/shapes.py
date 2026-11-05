"""The shapes trafilatura gives lists, tables and code: items, rows and cells through wrappers."""

import re

from clearmd.backend.services.conversion.xmltree import Element


def list_items(element: Element) -> list[Element]:
    """A list's items, through what wraps them (``<dl><div><dt>``, ``<ul><a><li>``); text or an
    element with no item inside becomes an item of its own, never lost."""
    found: list[Element] = []
    pending: list[Element | str] = list(reversed(element.children))
    while pending:
        node = pending.pop()
        if isinstance(node, str):
            if node.strip():
                found.append(Element("item", {}, [node]))
        elif node.tag == "item":
            found.append(node)
        elif node.tag != "list" and node.find("item") is not None:
            pending.extend(reversed(node.children))  # a wrapper: its items, in order
        else:
            found.append(Element("item", {}, [node]))  # a nested list, a paragraph…
    return found


def table_rows(table: Element) -> list[Element]:
    """A table's rows, through what wraps them (``<table><form><tr>``); a bare cell or text
    becomes a row of its own. Nested tables are their cells' content, not rows here."""
    found: list[Element] = []
    pending: list[Element | str] = list(reversed(table.children))
    while pending:
        node = pending.pop()
        if isinstance(node, str):
            if node.strip():
                found.append(Element("row", {}, [Element("cell", {}, [node])]))
        elif node.tag == "row":
            found.append(node)
        elif node.tag == "cell":
            found.append(Element("row", {}, [node]))
        elif node.tag == "table":  # a table inside the table, outside a cell: its text, apart
            found.append(Element("row", {}, [Element("cell", {}, [node])]))
        else:
            pending.extend(reversed(node.children))
    return found


def row_cells(row: Element) -> list[Element]:
    """A row's cells; text beside them becomes a cell of its own."""
    cells = []
    for node in row.children:
        if isinstance(node, Element) and node.tag == "cell":
            cells.append(node)
        elif isinstance(node, str) and node.strip() or isinstance(node, Element):
            cells.append(Element("cell", {}, [node]))
    return cells


def code_text(element: Element) -> str:
    """A code block's text as written, a line break for each ``lb``."""
    out: list[str] = []
    pending: list[Element | str] = [element]
    while pending:
        node = pending.pop()
        if isinstance(node, str):
            out.append(node)
        elif node.tag == "lb":
            out.append("\n")
        else:
            pending.extend(reversed(node.children))
    return "".join(out)


def one_line(text: str) -> str:
    """Text whose hard line breaks become one space (a heading, a cell, the title)."""
    return re.sub(r" *  \n *", " ", text)
