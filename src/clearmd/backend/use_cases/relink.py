"""A Markdown moved to another folder keeps its images (audit 2026-11-08, B1-12).

Split writes a Markdown's parts in OutputSep and Merge joins it in OutputUnif: a relative link
such as ``![](report_imagenes/image-001.png)`` would point at nothing there. Each relative link
to a file that exists next to the source is rewritten relative to the new folder; links to the
web, anchors, absolute paths and links that were already broken stay as they are.
"""

import os
import re
from pathlib import Path
from urllib.parse import quote, unquote

# ![alt](target "title") and [text](target), the target bare or in <...>; and "[id]: target".
_INLINE = re.compile(r"(\]\()(<[^>\n]+>|[^)\s]+)((?:\s+\"[^\"\n]*\")?\))")
_REFERENCE = re.compile(r"(?m)^( {0,3}\[[^\]\n]+\]:[ \t]*)(<[^>\n]+>|\S+)")
_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")


def _moved(target: str, source_dir: Path, new_dir: Path) -> str | None:
    bare = target[1:-1] if target.startswith("<") and target.endswith(">") else target
    path, hash_mark, anchor = bare.partition("#")
    if not path or _SCHEME.match(path) or path.startswith(("/", "\\")):
        return None
    found = source_dir / unquote(path)
    if not found.is_file():
        return None  # already broken where it was: nothing better to point at
    try:
        relative = os.path.relpath(found, new_dir)
    except ValueError:  # another drive (Windows): the full path
        relative = str(found)
    link = Path(relative).as_posix() + hash_mark + anchor
    if target.startswith("<") or " " in link:
        return f"<{link}>"
    return quote(link, safe="/#:.-_~()+,;=&@!$'*")


def relinked(text: str, source_dir: Path, new_dir: Path) -> str:
    """``text`` with its relative links made to work from ``new_dir``."""
    if source_dir == new_dir:
        return text

    def inline(match: re.Match[str]) -> str:
        moved = _moved(match.group(2), source_dir, new_dir)
        return match.group(0) if moved is None else match.group(1) + moved + match.group(3)

    def reference(match: re.Match[str]) -> str:
        moved = _moved(match.group(2), source_dir, new_dir)
        return match.group(0) if moved is None else match.group(1) + moved

    return _REFERENCE.sub(reference, _INLINE.sub(inline, text))
