"""Subtitles (SRT, WebVTT) to Markdown (feature 029, ADR-0049): each cue as a line with its start
time, so an AI reads the transcript and can still point at a moment. Standard library only."""

import re
from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.models import ConversionResult, Detection
from clearmd.backend.services.conversion.safe_files import NotARegularFile, read_regular_file

MAX_BYTES = 32 * 1024**2
_TIME = re.compile(r"^\s*((?:\d+:)?\d{1,2}:\d{2}[.,]\d{1,3})\s*-->\s*\S+")
_TAG = re.compile(r"<[^>]{1,200}>")  # <i>, <b>, <v Speaker>, <00:01.000>


def _start(stamp: str) -> str:
    """``00:01:02,500`` → ``00:01:02``; ``01:02.500`` → ``00:01:02``."""
    whole = re.split(r"[.,]", stamp)[0]
    parts = whole.split(":")
    if len(parts) == 2:
        parts.insert(0, "00")
    return ":".join(part.zfill(2) for part in parts)


def cues(text: str) -> list[tuple[str, str]]:
    """(start, text) of each cue; a cue's lines joined by a space, its tags removed."""
    found: list[tuple[str, str]] = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\r", "\n")):
        lines = [line for line in block.split("\n") if line.strip()]
        for index, line in enumerate(lines):
            time = _TIME.match(line)
            if time:
                words = " ".join(_TAG.sub("", rest).strip() for rest in lines[index + 1 :])
                if words.strip():
                    found.append((_start(time.group(1)), words.strip()))
                break
    return found


class SubtitlesConverter:
    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        try:
            data = read_regular_file(source, MAX_BYTES)
        except (OSError, NotARegularFile) as error:
            raise ConversionError(ErrorCode.SOURCE_UNREADABLE, str(error)) from error
        text = data.decode("utf-8-sig", errors="replace")
        found = cues(text)
        if not found and "-->" not in text:
            raise ConversionError(ErrorCode.CORRUPT_FILE, "no subtitle cues found")
        lines = [f"`{start}` {words}" for start, words in found]
        return ConversionResult("\n\n".join(lines) + ("\n" if lines else ""))
