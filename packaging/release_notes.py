"""The notes a release page shows (audit v3, B5-03): "What to Download", then only this version's
news. The whole history stays in packaging/RELEASE_NOTES.md, linked from the page.

    python packaging/release_notes.py > release-notes.md
"""

import sys
from pathlib import Path

NOTES = Path(__file__).with_name("RELEASE_NOTES.md")
VERSION_HEADING = "**New in "


def published(notes: str) -> str:
    """The header and the newest version's section: up to the second version heading."""
    first = notes.index(VERSION_HEADING)
    second = notes.find(VERSION_HEADING, first + len(VERSION_HEADING))
    return (notes if second < 0 else notes[:second]).rstrip() + "\n"


if __name__ == "__main__":
    sys.stdout.write(published(NOTES.read_text(encoding="utf-8")))
