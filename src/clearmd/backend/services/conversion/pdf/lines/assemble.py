"""One line from a run of characters: its text, size, weight and place (feature 008, 014)."""

from collections import Counter

from clearmd.backend.services.conversion.pdf.decode import LINE_END, SKIPPED, SOFT_HYPHENS, decoded
from clearmd.backend.services.conversion.pdf.lines.scripts import scripted
from clearmd.backend.services.conversion.pdf.lines.words import build_word
from clearmd.backend.services.conversion.pdf.model import (
    ASLANT,
    SOFT_HYPHEN,
    UNREADABLE,
    Chars,
    Document,
    Line,
)
from clearmd.backend.services.conversion.pdf.tables import Word


def build_line(
    chars: Chars,
    span: range,
    shifts: list[int],
    unmapped: list[bool],
    document: Document,
    words: dict[int, list[Word]] | None = None,
) -> Line:
    pieces: list[tuple[str, int]] = []  # each piece of text and the character it comes from
    word: list[int] = []  # the indices of the word being read, and its text
    word_text: list[str] = []

    def put(piece: str, index: int = -1) -> None:
        pieces.append((piece, index))

    def end_word() -> None:
        turn = chars.turns[word[0]] if word else ASLANT
        if words is not None and turn in words and chars.turns[word[-1]] == turn:
            words[turn].append(build_word("".join(word_text), chars, word, turn))
        word.clear()
        word_text.clear()

    high = 0  # PDFium gives a character past U+FFFF as two halves (a surrogate pair)
    visible: list[int] = []
    for index in span:
        font = chars.fonts[index]
        raw_code = chars.codes[index]
        if raw_code in SKIPPED:
            continue
        if raw_code == LINE_END:  # one PDFium ended where the row goes on: a space between
            put(" ")  # (gone if it touches a script: "Rᴺ" and "₊")
            end_word()
            continue
        code = decoded(raw_code, shifts[font])
        if high and not 0xDC00 <= code < 0xE000:  # a first half with no second: unreadable
            document.unreadable += 1
            put(UNREADABLE)
            high = 0
        if 0xD800 <= code < 0xDC00:
            high = code
            continue
        if 0xDC00 <= code < 0xE000:
            if high:
                put(chr(0x10000 + ((high - 0xD800) << 10) + (code - 0xDC00)), index)
            else:
                document.unreadable += 1
                put(UNREADABLE, index)
            high = 0
            visible.append(index)
            word.append(index)
            word_text.append(pieces[-1][0])
            continue
        if code in SOFT_HYPHENS:
            put(SOFT_HYPHEN, index)
        elif code == 0x09 or code == 0x20:
            put(" ")
            end_word()
            continue
        elif code < 0x20 or code == 0x7F or code > 0x10FFFF or code == 0xFFFD:
            # A code no map turned into a character: never dropped silently (ADR-0022).
            document.unreadable += 1
            put(UNREADABLE, index)
        elif unmapped[font] and not shifts[font]:
            document.unreadable += 1  # a font without a map, not read back: its letters are wrong
            put(chr(code), index)
        else:
            put(chr(code), index)
        visible.append(index)
        word.append(index)
        word_text.append(pieces[-1][0])
    if high:
        document.unreadable += 1
        put(UNREADABLE)
    end_word()
    shown = visible or list(span)
    sizes = Counter(round(chars.sizes[index], 1) for index in shown)
    return Line(
        " ".join(scripted(pieces, chars, visible).split()),
        sizes.most_common(1)[0][0],
        sum(chars.bold[index] for index in shown) * 2 > len(shown),
        max(chars.tops[index] for index in shown),
        min(chars.bottoms[index] for index in shown),
        turn=Counter(chars.turns[index] for index in shown).most_common(1)[0][0],
        left=min(chars.lefts[index] for index in shown),
        right=max(chars.rights[index] for index in shown),
        span=(span.start, span.stop),
    )
