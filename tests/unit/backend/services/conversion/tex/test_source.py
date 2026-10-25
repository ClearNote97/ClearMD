"""Reading a .tex file's text (AC-20)."""

import pytest
from support import TEX_DIR

from clearmd.backend.services.conversion.tex.source import decode_source


def test_utf8_is_read_as_is_and_a_bom_is_dropped() -> None:
    text = decode_source("\ufeff\\section{Introducción}".encode())
    assert (text.text, text.encoding, text.guessed) == ("\\section{Introducción}", "utf-8", False)


def test_the_encoding_declared_with_inputenc_is_used() -> None:
    text = decode_source((TEX_DIR / "latin1.tex").read_bytes())
    assert "Cañón, acción y ñandú" in text.text
    assert (text.encoding, text.guessed) == ("latin-1", False)


def test_an_undeclared_encoding_is_detected_and_marked_as_guessed() -> None:
    text = decode_source((TEX_DIR / "latin1_undeclared.tex").read_bytes())
    assert "Cañón, acción y ñandú" in text.text
    assert text.guessed


@pytest.mark.parametrize(("option", "codec"), [("cp1252", "cp1252"), ("ansinew", "cp1252")])
def test_windows_encodings_are_understood(option: str, codec: str) -> None:
    data = f"\\usepackage[{option}]{{inputenc}}\n“comillas”".encode(codec)
    text = decode_source(data)
    assert "“comillas”" in text.text
    assert not text.guessed


def test_nothing_readable_still_gives_text() -> None:
    text = decode_source(bytes(range(128, 256)))
    assert isinstance(text.text, str)
    assert text.guessed
