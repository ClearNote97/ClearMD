"""Feature 023 — Split's choices remembered (AC-10), and its texts in both languages with titles
and buttons in Title Case (AC-11)."""

import pytest

from clearmd.backend.schemas.settings import Settings
from clearmd.backend.use_cases.settings import parse_settings, serialize_settings
from clearmd.i18n import load_catalog

from .test_021_flet_start_tiles import SMALL

# Titles and buttons of feature 023: the start screen, Split's block and setting, and Split's own
# words in place of Convert's.
TITLES = (
    "gui.home.title",
    "gui.home.convert",
    "gui.home.split",
    "gui.home.step",
    "gui.split.title",
    "gui.settings.split",
    "gui.page.choose_title",
    "gui.page.review_title",
    "gui.page.convert_title",
    "gui.steps.convert",
    "gui.main.convert",
    "gui.plan.confirm",
    "gui.plan.stat_convert",
    "gui.progress.current",
    "gui.result.stat_converted",
    "gui.result.again",
    "gui.more.title",
    "summary.split_done",
)
SECTIONS = ("gui.home.", "gui.split.", "tool.split.", "summary.split", "summary.parts", "split.")


def test_ac_10_the_cut_and_what_to_keep_are_remembered() -> None:
    chosen = Settings(split_cut="pages", split_parts=7, split_pages=25, split_keep="markdown")
    settings, warnings = parse_settings(serialize_settings(chosen))
    assert settings == chosen and warnings == ()
    assert Settings().split_cut == "parts" and Settings().split_keep == "both"


@pytest.mark.parametrize(
    "line",
    [
        "split_parts = 1",  # fewer than 2 parts
        "split_pages = 0",
        "split_pages = 10001",
        "split_parts = true",  # a boolean is not a number
        'split_parts = "4"',
        'split_cut = "lines"',
        'split_keep = "zip"',
    ],
)
def test_ac_10_a_wrong_split_setting_falls_back_to_its_default(line: str) -> None:
    settings, warnings = parse_settings(line + "\n")
    assert settings == Settings()
    assert [warning.key for warning in warnings] == [line.split()[0]]


def test_ac_10_a_wrong_split_setting_is_never_written() -> None:
    with pytest.raises(ValueError):
        serialize_settings(Settings(split_parts=1))


def test_ac_11_both_languages_have_every_text_of_split() -> None:
    english, spanish = load_catalog("en"), load_catalog("es")
    mine = {key for key in english.keys() if key.startswith(SECTIONS)}
    assert len(mine) > 40
    assert mine == {key for key in spanish.keys() if key.startswith(SECTIONS)}
    for key in mine:
        assert spanish.text_template(key) != "" and english.text_template(key) != ""


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_11_titles_and_buttons_are_in_title_case(language: str) -> None:
    catalog = load_catalog(language).for_tool("split")
    for key in TITLES:
        title = catalog.text_template(key)
        words = [word.lstrip("¿¡(") for word in title.split()]
        for position, word in enumerate(words):
            if not word[:1].isalpha():
                continue
            if position > 0 and word.lower() in SMALL:
                assert word == word.lower(), (key, title, word)
            else:
                assert word[0].isupper(), (key, title, word)


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_11_split_speaks_in_place_of_convert_only_where_it_must(language: str) -> None:
    convert, split = load_catalog(language), load_catalog(language).for_tool("split")
    assert convert.text("gui.page.choose_title") != split.text("gui.page.choose_title")
    assert convert.text("gui.main.add_files") == split.text("gui.main.add_files")
    assert convert.for_tool("convert") is convert  # Convert is the catalog itself
