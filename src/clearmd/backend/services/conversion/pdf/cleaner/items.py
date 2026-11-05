"""The markers a list item starts with (008)."""

import re

BULLET = re.compile(r"[•●▪■◦‣∙·](?=\s)\s*")  # always a list item
DASH = re.compile(r"[-–*](?=\s)\s*")  # an item only where no sentence goes on
CIRCLE = re.compile(r"o(?=\s)\s*")  # Word's second-level bullet, only inside a list
