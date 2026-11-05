"""The measures and the sentence end that more than one cleaner module reads."""

import re

HEADING_RATIO = 1.2  # this much taller than the body text
MAX_LEVEL = 4
PARAGRAPH_GAP = 0.8  # a blank this many line heights tall starts a paragraph


SENTENCE_END = re.compile(r"[.!?:;…\"”»)]$")
