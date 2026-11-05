"""An equation's pieces rebuilt as LaTeX (feature 015, ADR-0036): pure geometry in, LaTeX out."""

from clearmd.backend.services.conversion.pdf import blocks, model
from clearmd.backend.services.conversion.pdf.equations import Placed, find_equations
from clearmd.backend.services.conversion.pdf.latex import (
    MAX_GLYPHS,
    Bar,
    Glyph,
    to_latex,
)
from clearmd.backend.services.conversion.pdf.latex.envelope import balanced
from clearmd.backend.services.conversion.pdf.tables import Word

SIZE = 10.0


def text(chars: str, x: float, baseline: float, size: float = SIZE) -> list[Glyph]:
    """Characters set from ``x`` on one baseline, each half its size wide (tight boxes)."""
    out = []
    for char in chars:
        width = 0.5 * size
        out.append(Glyph(char, x, x + width, baseline - 0.05 * size, baseline + 0.7 * size,
                         size, baseline))  # fmt: skip
        x += width
    return out


def tall(char: str, x: float, bottom: float, top: float) -> Glyph:
    """A bracket or a sum drawn taller than the text (its baseline is no measure)."""
    return Glyph(char, x, x + 4, bottom, top, SIZE, bottom)


def test_a_fraction_from_its_bar() -> None:
    glyphs = [*text("C=", 0, 100), *text("ab", 14, 106), *text("c", 16, 94)]
    assert to_latex(glyphs, [Bar(13, 25, 102.5)]) == r"C= \frac{ab}{c}"


def test_scripts_raised_and_lowered_on_one_base() -> None:
    glyphs = [
        *text("EF", 0, 100),
        *text("t+1", 10, 104, size=6),
        *text("o", 10, 97, size=6),
        *text("=x", 22, 100),
    ]
    assert to_latex(glyphs, []) == r"EF_{o}^{t+1} =x"


def test_a_tall_bracket_holds_its_fractions_and_takes_a_script() -> None:
    glyphs = [
        tall("[", 0, 90, 116),
        *text("a", 6, 106),
        *text("b", 6, 94),
        tall("]", 14, 90, 116),
        *text("2", 19, 112, size=6),
    ]
    assert to_latex(glyphs, [Bar(5, 12, 102.5)]) == r"\left[ \frac{a}{b} \right]^{2}"


def test_a_sum_with_its_limits_above_and_below() -> None:
    glyphs = [
        tall("∑", 0, 95, 112),
        *text("J", 1, 114, size=6),
        *text("j=1", 0, 90, size=6),
        *text("z", 14, 100),
        *text("j", 19, 97, size=6),
    ]
    assert to_latex(glyphs, []) == r"\sum_{j=1}^{J} z_{j}"


def test_the_number_at_the_right_is_its_tag() -> None:
    glyphs = [*text("y=x", 0, 100), *text("(12)", 200, 100)]
    assert to_latex(glyphs, []) == r"y=x \tag{12}"


def test_rows_of_a_system_and_words_inside() -> None:
    glyphs = [*text("Max", 0, 120), *text("x", 20, 120), *text("if", 30, 100), *text("x", 42, 100)]
    latex = to_latex(glyphs, [])
    rows = r"\displaystyle \operatorname*{Max} x \\ \displaystyle \text{ if } x"
    assert latex == rf"\begin{{array}}{{l}} {rows} \end{{array}}"


def test_a_brace_with_no_closing_one_holds_the_rest() -> None:
    glyphs = [*text("P=", 0, 100), tall("{", 12, 85, 120), *text("a", 18, 110),
              *text("b", 18, 90)]  # fmt: skip
    assert (
        to_latex(glyphs, [])
        == r"P= \left\{ \begin{array}{l} \displaystyle a \\ \displaystyle b \end{array} \right."
    )


def test_an_overline_a_root_and_a_minus_drawn_as_lines() -> None:
    assert to_latex(text("ab", 0, 100), [Bar(0, 10, 108)]) == r"\overline{ab}"
    root = [Glyph("√", 0, 5, 96, 109, SIZE, 98), *text("x", 6, 100)]
    assert to_latex(root, [Bar(5, 11, 108)]) == r"\sqrt{x}"
    minus = [*text("a", 0, 100), *text("b", 16, 100)]
    assert to_latex(minus, [Bar(7, 13, 102.5)]) == "a - b"


def test_symbols_and_math_letters_as_commands() -> None:
    glyphs = text("𝜃≤∞", 0, 100)
    assert to_latex(glyphs, []) == r"\theta\leq\infty"


def test_unsure_gives_none() -> None:
    assert to_latex([], []) is None
    assert to_latex(text("a�b", 0, 100), []) is None
    assert to_latex(text("x" * (MAX_GLYPHS + 1), 0, 100), []) is None


def test_balanced_braces_brackets_and_environments() -> None:
    assert balanced(r"\left[ \frac{a}{b} \right] \{ x \}")
    assert not balanced(r"\frac{a}{b")
    assert not balanced(r"\left[ a")
    assert not balanced(r"\begin{array}{l} a")


def _line(text: str, bottom: float, left: float, right: float) -> Placed:
    return Placed(text, bottom + SIZE, bottom, SIZE, right, False, left)


def _word(text: str, left: float, bottom: float) -> Word:
    return Word(text, left, left + 5 * len(text), bottom, bottom + SIZE, SIZE)


def test_an_equation_with_no_number_found_by_its_fraction_bar() -> None:
    lines = [
        _line("The change is then measured as follows for each firm:", 130, 72, 400),
        _line("C = ab", 103, 150, 200),
        _line("c", 92, 185, 190),
        _line("where the variables are the ones defined in the text above it.", 60, 72, 400),
    ]
    words = [_word("C", 150, 100), _word("=", 160, 100), _word("ab", 182, 105),
             _word("c", 185, 92)]  # fmt: skip
    assert find_equations(lines, words, [(180, 195, 103.0)]) == [range(1, 3)]


def test_a_bar_with_no_relation_or_repeated_as_a_tables_rows_is_no_equation() -> None:
    lines = [_line("N", 103, 150, 160), _line("45", 92, 150, 160)]
    words = [_word("N", 150, 105), _word("45", 150, 92)]
    assert find_equations(lines, words, [(148, 162, 103.0)]) == []
    lines = [_line("a = b", 103, 150, 175), _line("c", 92, 150, 160)]
    words = [_word("a", 150, 105), _word("=", 157, 105), _word("b", 165, 105),
             _word("c", 152, 92)]  # fmt: skip
    ruled = [(148, 178, 103.0), (148, 178, 120.0)]
    assert find_equations(lines, words, ruled) == []


# --- The review of 015 ----------------------------------------------------------------------


def test_many_sizes_none_shared_is_no_failure() -> None:
    glyphs = [
        g for n, char in enumerate("y=a+b+c+d+e+") for g in text(char, n * 6, 100, 9 + n * 0.3)
    ]
    assert to_latex(glyphs, []) is not None


def test_a_numerator_never_takes_the_row_above() -> None:
    glyphs = [*text("uvw=k", 0, 116), *text("C=", 0, 100), *text("ab", 14, 106),
              *text("c", 16, 94)]  # fmt: skip
    latex = to_latex(glyphs, [Bar(13, 25, 102.5)])
    assert latex is not None and r"\frac{ab}{c}" in latex and "uvw=k" in latex


def test_degrees_primes_and_accents_as_katex_reads_them() -> None:
    squared = [*text("x", 0, 100), *text("2", 5, 104, size=6)]
    assert to_latex([*squared, *text("°", 9, 100)], []) == r"x^{2}{}^{\circ}"
    assert to_latex([*squared, *text("′", 9, 100)], []) == "x^{2}{}'"
    hat = Glyph("ˆ", 0.5, 4.5, 108, 110, SIZE, 104)
    assert to_latex([*text("x", 0, 100), hat], []) == r"\hat{x}"
    assert to_latex([*text("x", 0, 100), Glyph("ˆ", 20, 24, 108, 110, SIZE, 104)], []) is None
    assert to_latex(text("a‮b", 0, 100), []) is None  # a direction change: unseen


def test_limits_under_a_word_merged() -> None:
    glyphs = [*text("Max", 0, 100), *text("z", 0.5, 90, size=6), *text("q", 10.5, 90, size=6)]
    assert to_latex(glyphs, []) == r"\operatorname*{Max}_{z q}"


def test_drawn_lines_capped_and_an_equals_sign_drawn_as_two() -> None:
    assert to_latex(text("ab", 0, 100), [Bar(20, 22, 50 + n) for n in range(65)]) is None
    glyphs = [*text("a", 0, 100), *text("b", 16, 100)]
    assert to_latex(glyphs, [Bar(7, 13, 101.5), Bar(7, 13, 104.0)]) == "a = b"


def test_tall_bars_pair_and_letters_stay_variables() -> None:
    glyphs = [*text("D=", 0, 100), tall("|", 12, 90, 116), *text("a", 18, 106), *text("b", 18, 94),
              tall("|", 26, 90, 116)]  # fmt: skip
    assert to_latex(glyphs, [Bar(17, 24, 102.5)]) == r"D= \left| \frac{a}{b} \right|"
    assert to_latex(text("y=abc", 0, 100), []) == "y=abc"


def test_a_numbered_equation_keeps_its_rows_of_named_variables() -> None:
    lines = [
        _line("Profit Revenue Costs", 103, 150, 300),
        _line("P = R - C (4)", 90, 150, 520),
    ]
    words = [_word("(4)", 505, 90), _word("C", 200, 90)]
    assert find_equations(lines, words) == [range(0, 2)]


def test_a_footnote_rule_is_no_fraction_bar() -> None:
    lines = [
        _line("so that y = 2x.", 103, 72, 160),
        Placed("1 let a = b.", 98, 90, 8.0, 140, False, 72),
    ]
    words = [_word("so", 72, 103), _word("y", 100, 103), _word("=", 110, 103),
             Word("let", 80, 95, 90, 98, 8.0), Word("a", 100, 105, 90, 98, 8.0)]  # fmt: skip
    assert find_equations(lines, words, [(72, 130, 100.0)]) == []


def _chars(codes: list[int]) -> model.Chars:
    chars = model.Chars()
    for n, code in enumerate(codes):
        chars.codes.append(code)
        chars.fonts.append(0)
        chars.sizes.append(SIZE)
        chars.bottoms.append(99.0)
        chars.tops.append(107.0)
        chars.lefts.append(n * 5.0)
        chars.rights.append(n * 5.0 + 5)
        chars.turns.append(model.UPRIGHT)
        chars.font_sizes.append(SIZE)
        chars.baselines.append(100.0)
        chars.bold.append(0)
    return chars


def _latex_of(codes: list[int], *, unmapped: bool = False) -> str:
    chars = _chars(codes)
    line = model.Line("", SIZE, False, 107, 99, span=(0, len(codes)), right=5.0 * len(codes))
    found = blocks.equation_latex.Found(chars, [0], [unmapped], [])
    return blocks.equation_latex.latex_of([line], found, (99, 107, 0, 5.0 * len(codes)))


def test_an_unreadable_or_unmapped_glyph_makes_it_unsure() -> None:
    assert _latex_of([ord("a"), ord("="), ord("b")]) == "a=b"
    assert _latex_of([ord("a"), 0x01, ord("b")]) == ""  # a code no map turned into a letter
    assert _latex_of([ord("a"), 0xD835, ord("b")]) == ""  # half a character
    assert _latex_of([0xD835, 0xDC00, ord("b")]) == "Ab"  # 𝐀, whole
    assert _latex_of([ord("a"), ord("b")], unmapped=True) == ""
