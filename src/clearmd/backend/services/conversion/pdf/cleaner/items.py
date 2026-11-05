"""A list item: the markers it starts with, and the text after one (008)."""

import re

from clearmd.backend.services.conversion.pdf.cleaner.flow import Flow, sentence_ended
from clearmd.backend.services.conversion.pdf.model import Line

BULLET = re.compile(r"[•●▪■◦‣∙·](?=\s)\s*")  # always a list item
DASH = re.compile(r"[-–*](?=\s)\s*")  # an item only where no sentence goes on
CIRCLE = re.compile(r"o(?=\s)\s*")  # Word's second-level bullet, only inside a list


def list_item(flow: Flow, line: Line) -> str | None:
    """The text after the line's list marker; None when the line is no item."""
    text = line.text
    if bullet := BULLET.match(text):
        return text[bullet.end() :]
    mid_sentence = flow.kind == "text" and not sentence_ended(flow)
    if (dash := DASH.match(text)) and not mid_sentence:
        return text[dash.end() :]
    if (circle := CIRCLE.match(text)) and flow.kind == "item":
        return text[circle.end() :]
    return None
