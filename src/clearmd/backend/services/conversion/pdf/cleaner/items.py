"""A list item: the markers it starts with, and the text after one (008)."""

import re

from clearmd.backend.services.conversion.pdf.cleaner.flow import Flow, sentence_ended
from clearmd.backend.services.conversion.pdf.model import Line

BULLET = re.compile(r"[•●▪■◦‣∙·](?=\s)\s*")  # always a list item
DASH = re.compile(r"[-–*](?=\s)\s*")  # an item only where no sentence goes on
CIRCLE = re.compile(r"o(?=\s)\s*")  # Word's second-level bullet, only inside a list
# "1.", "2)", "10.", "a)", "b.": an item where no sentence goes on (audit v4, B3-01).
ORDERED = re.compile(r"(\d{1,3}|[a-z])([.)])(?=\s)\s*")


def list_item(flow: Flow, line: Line) -> tuple[str, str] | None:
    """The item's marker as it is written ("- ", "3. ") and its text; None when no item."""
    text = line.text
    if bullet := BULLET.match(text):
        return "- ", text[bullet.end() :]
    mid_sentence = flow.kind == "text" and not sentence_ended(flow)
    if (dash := DASH.match(text)) and not mid_sentence:
        return "- ", text[dash.end() :]
    if (circle := CIRCLE.match(text)) and flow.kind == "item":
        return "- ", text[circle.end() :]
    if (
        (ordered := ORDERED.match(text))
        and not mid_sentence
        and text[ordered.end() :][:1].isupper()
    ):
        number, sign = ordered.groups()
        if number.isdigit():
            return f"{int(number)}. ", text[ordered.end() :]
        return "- ", f"{number}{sign} {text[ordered.end() :]}"
    return None
