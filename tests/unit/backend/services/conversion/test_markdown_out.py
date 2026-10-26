"""The shared output guarantee (ADR-0023, ADR-0024), on its own: every converter relies on it."""

import pytest

from clearmd.backend.services.conversion.markdown_out import (
    MARK,
    escape_math,
    escape_text,
    inline_code,
    join_pieces,
    link_target,
    marked,
    neutralize,
    outside_code,
)


def test_document_text_never_becomes_a_link_html_or_a_code_span() -> None:
    assert escape_text("<img> [a](b) `x`") == "&lt;img> &#91;a&#93;(b) \\`x\\`"
    # A backslash is doubled only before what it could escape: "\\section" stays as written.
    assert escape_text("\\` \\section \\|") == "\\\\\\` \\section \\\\|"
    assert escape_text("a\\") + escape_text("`") == "a\\\\\\`"  # across pieces too
    assert MARK not in escape_text(f"a{MARK}b")


def test_math_keeps_its_meaning_and_loses_its_markdown() -> None:
    assert escape_math("a <img b ![x](y) `") == "a < img b ! [x] (y) &#96;"
    assert escape_math("a < b") == "a < b"


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("# h", "\\# h"),
        ("> q", "\\> q"),
        ("- i", "\\- i"),
        ("1. i", "1\\. i"),
        ("===", "\\==="),
        ("--", "\\--"),
        ("***", "\\***"),
        ("```", "\\```"),
        ("[a]: http://x", "\\[a]: http://x"),
        ("| a | b |", "\\| a | b |"),
        ("plain", "plain"),
    ],
)
def test_a_line_the_document_wrote_is_never_a_block(line: str, expected: str) -> None:
    assert neutralize(f"text\n{line}") == f"text\n{expected}"


def test_a_code_span_at_the_start_of_a_line_is_not_a_fence() -> None:
    line = "``` ``<img src=x>! ``` after"
    assert neutralize(f"text\n{line}") == f"text\n{line}"
    assert neutralize("text\n```py") == "text\n\\```py"


def test_clearmds_own_marked_lines_and_their_code_stay() -> None:
    text = f"{MARK}## h\n{MARK}```\n# inside code\n{MARK}```\n# after"
    assert neutralize(text) == "## h\n```\n# inside code\n```\n\\# after"


def test_an_indented_line_after_a_blank_is_never_code() -> None:
    assert neutralize("a\n\n    code\n\n\t\tcode") == "a\n\ncode\n\ncode"


def test_neighbours_never_form_what_none_of_them_wrote() -> None:
    assert join_pieces(["!", "[@a]", "(x)", "`a`", "`b`"]) == "\\![@a]\\(x)`a` `b`"


def test_code_spans_are_one_line_and_survive_backticks() -> None:
    assert inline_code("a\n\nb") == "`a b`"
    assert inline_code("a`b") == "`` a`b ``"


def test_outside_code_leaves_marked_fences_alone() -> None:
    text = f"x\n\n\n{MARK}```\na\n\n\nb\n{MARK}```\n\n\ny"
    fixed = outside_code(text, lambda part: part.replace("\n\n\n", "\n\n"))
    assert "a\n\n\nb" in fixed and "x\n\n" in fixed


def test_link_targets_stay_one_destination() -> None:
    assert link_target("a b(1).png") == "<a b(1).png>"
    assert link_target("plain.png") == "plain.png"
    assert marked("a\nb") == f"{MARK}a\n{MARK}b"
