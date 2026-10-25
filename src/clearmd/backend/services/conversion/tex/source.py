"""The text of a .tex file: UTF-8, else the encoding inputenc declares, else a detected one."""

import re
from dataclasses import dataclass

import charset_normalizer

# inputenc options → Python codecs (the ones found in real theses).
INPUTENC_CODECS = {
    "utf8": "utf-8",
    "latin1": "latin-1",
    "latin9": "iso-8859-15",
    "cp1252": "cp1252",
    "ansinew": "cp1252",
    "applemac": "mac_roman",
    "cp850": "cp850",
}
# On a tie, ClearMD's audience (Spanish and English) means Western European: a short Spanish text
# scores the same in cp1250 ("Cańón") as in cp1252 ("Cañón").
PREFERRED_ON_TIE = ("cp1252", "latin_1", "iso8859_15", "mac_roman")
_INPUTENC = re.compile(rb"\\usepackage\s*\[([^\]\n]{0,256})\]\s*\{inputenc\}")


@dataclass(frozen=True)
class SourceText:
    text: str
    encoding: str
    guessed: bool


def _declared_codec(data: bytes) -> str | None:
    match = _INPUTENC.search(data)
    if match is None:
        return None
    for option in match.group(1).decode("ascii", errors="ignore").split(","):
        codec = INPUTENC_CODECS.get(option.strip().lower())
        if codec is not None:
            return codec
    return None


def decode_source(data: bytes) -> SourceText:
    try:
        return SourceText(data.decode("utf-8-sig"), "utf-8", guessed=False)
    except UnicodeDecodeError:
        pass
    codec = _declared_codec(data)
    if codec == "latin-1":
        # Typed on Windows, "latin1" text holds cp1252 quotes and dashes (0x80-0x9F), which
        # latin-1 would turn into invisible control characters.
        try:
            return SourceText(data.decode("cp1252"), "cp1252", guessed=False)
        except UnicodeDecodeError:
            pass
    if codec is not None and codec != "utf-8":
        try:
            return SourceText(data.decode(codec), codec, guessed=False)
        except UnicodeDecodeError:
            pass
    candidates = list(charset_normalizer.from_bytes(data))
    if candidates:
        best = candidates[0]
        tied = [c for c in candidates if (c.chaos, c.coherence) == (best.chaos, best.coherence)]
        chosen = next((c for c in tied if c.encoding in PREFERRED_ON_TIE), best)
        return SourceText(str(chosen), chosen.encoding, guessed=True)
    return SourceText(data.decode("latin-1"), "latin-1", guessed=True)
