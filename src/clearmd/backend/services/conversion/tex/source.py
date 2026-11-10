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
# What a Western text saved by Windows (cp1252) holds beyond ASCII: the letters of Spanish, English,
# French, Portuguese, German and Italian, and their typographic punctuation (audit v3, B1-01).
WESTERN = frozenset(
    "áéíóúýàèìòùâêîôûãõäëïöüÿñçœæåøßÁÉÍÓÚÝÀÈÌÒÙÂÊÎÔÛÃÕÄËÏÖÜŸÑÇŒÆÅØ"
    "¿¡«»“”‘’‚„–—…€•·°ºª§©®™×÷±²³¼½¾£¥¢¤¦¨¯´¸¹µ¶ \u00a0†‡‰‹›ˆ˜šŠžŽƒ"
)
# Western text is mostly ASCII: when more than this share of its letters are not, it is another
# script decoded wrongly (Cyrillic saved as cp1251 reads as "Ïðèâåò" in cp1252).
MAX_NON_ASCII_LETTERS = 0.3
SHORT_ALLOWANCE = 2
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
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):  # a byte-order mark says it (B1-10)
        try:
            return SourceText(data.decode("utf-16"), "utf-16", guessed=False)
        except UnicodeDecodeError:
            pass
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
    western = _as_western(data)
    if western is not None:
        return SourceText(western, "cp1252", guessed=True)
    candidates = list(charset_normalizer.from_bytes(data))
    if candidates:
        best = candidates[0]
        tied = [c for c in candidates if (c.chaos, c.coherence) == (best.chaos, best.coherence)]
        chosen = next((c for c in tied if c.encoding in PREFERRED_ON_TIE), best)
        return SourceText(str(chosen), chosen.encoding, guessed=True)
    return SourceText(data.decode("latin-1"), "latin-1", guessed=True)


def _as_western(data: bytes) -> str | None:
    """The text as Windows saves Western languages (cp1252), when it reads as such; else None.

    A detector scores short texts badly ("Canción" came out as cp775, "José;Bogotá" as johab), so
    the encoding ClearMD's audience uses most is tried first, and kept only when every character
    beyond ASCII is a Western letter or punctuation mark, and most letters are plain ASCII.
    """
    try:
        text = data.decode("cp1252")
    except UnicodeDecodeError:
        return None
    letters = 0
    beyond = 0
    for char in text:
        if char.isalpha():
            letters += 1
        if ord(char) < 0x80:
            if ord(char) < 0x20 and char not in "\t\n\r\f":
                return None  # a control character: binary or another encoding
            continue
        if char not in WESTERN:
            return None
        if char.isalpha():
            beyond += 1
    # A very short note ("Sí", "¿Qué?") is mostly accents: two such letters are always allowed,
    # or a detector reads it as Chinese (audit v4, B5-03).
    if letters and beyond > SHORT_ALLOWANCE and beyond / letters > MAX_NON_ASCII_LETTERS:
        return None
    return text
