"""The summary format (009) and the hint on every page (011)."""

from pathlib import Path

from support.presenter_fakes import make, state


def test_the_summary_format_is_chosen_remembered_and_sent_to_the_batch() -> None:
    presenter, view, fake, _ = make()
    assert view.last("output").summary_format == "markdown"
    presenter.choose_summary_format("markdown_pdf")
    assert fake.settings.summary_format == "markdown_pdf"
    assert view.last("output").summary_format == "markdown_pdf"
    presenter.choose_summary_format("docx")  # not a format: nothing changes
    assert fake.settings.summary_format == "markdown_pdf"
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    presenter.go_to(3)
    presenter.press_primary(False)
    view.drain()
    assert fake.run_calls[-1]["summary_pdf"] is True


# --- Feature 011: the hint says what is missing on every page ----------------------------------


def test_with_nothing_chosen_every_page_says_to_choose_first() -> None:
    presenter, view, _, _ = make()
    for page in (2, 3, 4):
        presenter.go_to(page)
        assert state(view).primary.hint == "Nothing chosen yet: add files or folders on Choose."
    presenter.add_paths([Path("/docs")])
    presenter.go_to(2)
    assert state(view).primary.hint == "Press Next on Choose to see what will happen."
