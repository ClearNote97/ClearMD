"""ClearMD's PDF converter: tables found without rules."""

from support.pdf_tables import DATA, grid

from clearmd.backend.services.conversion.pdf.tables import Word, find_tables


def test_a_table_is_found_with_its_rows_and_columns() -> None:
    (table,) = find_tables(grid(DATA))
    assert table.rows[0] == ("Year", "Median", "CV", "Maximum")
    assert table.rows[2] == ("2013", "0.861", "0.113", "1.0 (3)")
    assert table.top > table.bottom


def test_a_missing_cell_stays_empty() -> None:
    rows = [row[:] for row in DATA]
    rows[3][2] = ""
    (table,) = find_tables(grid(rows))
    assert table.rows[3] == ("2014", "0.863", "", "1.0 (4)")


def test_three_rows_are_no_table() -> None:
    assert find_tables(grid(DATA[:3])) == []


def test_prose_with_wide_gaps_is_no_table() -> None:
    words = []
    for index, xs in enumerate(((72, 200, 330), (90, 260, 400), (72, 150, 380), (120, 240, 300))):
        bottom = 700 - 14 * index
        for x in xs:
            words.append(Word("justified", x, x + 45, bottom, bottom + 10, 10))
    assert find_tables(words) == []  # gaps that do not line up


def test_an_aligned_formula_is_no_table() -> None:
    rows = [["x", "=", "t+1"], ["y", "=", "(10)"], ["z", "=", "a"], ["w", "=", "b"]]
    assert find_tables(grid(rows, columns=(72, 120, 200))) == []


def test_a_number_of_one_digit_is_content() -> None:
    rows = [["Year", "Effic.", "%"], ["2012", "3", "9"], ["2013", "3", "9"], ["2014", "5", "15"]]
    rows.append(["2015", "7", "21"])
    (table,) = find_tables(grid(rows, columns=(72, 180, 260)))
    assert table.rows[1] == ("2012", "3", "9")


def test_a_cell_wrapped_over_lines_stays_in_the_table() -> None:
    rows = [row[:] for row in DATA]
    rows.insert(2, ["", "", "", "(continued)"])
    rows.insert(3, ["", "", "", "(and more)"])
    (table,) = find_tables(grid(rows))
    # One cell, as ADR-0034 promises (audit 2026-11-09, B3-01): its lines join the row above.
    assert len(table.rows) == 5
    assert table.rows[1][3].endswith("(continued) (and more)")


def test_a_grouped_first_column_keeps_its_rows() -> None:
    rows = [row[:] for row in DATA]
    rows[2][0] = ""  # a year left blank under the one above: most cells filled, a row of its own
    (table,) = find_tables(grid(rows))
    assert len(table.rows) == len(DATA)


def test_a_bulleted_list_set_with_tabs_is_no_table() -> None:
    rows = [
        ["•", "Name", "Ana"],
        ["•", "Role", "Judge"],
        ["•", "Court", "Lima"],
        ["•", "Year", "2021"],
    ]
    assert find_tables(grid(rows, columns=(72, 90, 200))) == []
