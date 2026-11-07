"""Feature 005 — Choosing and planning (AC-05 to AC-08); spec/features/005_*/spec.md.

The window runs under a display (a virtual one when there is none), mostly on a fake backend.
"""

from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog
from types import SimpleNamespace

import pytest
from support.gui_fakes import FakeBackend, MemoryBackend, planned
from support.ttk_acceptance import (
    QUIET,
    confirm,
    converted,
    copy_documents,
    pump,
    replace_settings,
    to_review,
)

from clearmd.backend.schemas.models import BatchPlan
from clearmd.frontend.ttk import TtkApp


def test_ac_05_add_files_add_folder_drop_remove_and_no_duplicates(
    window: Callable[..., TtkApp], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first, second = tmp_path / "a.pdf", tmp_path / "b.docx"
    monkeypatch.setattr(filedialog, "askopenfilenames", lambda **_: (str(first), str(second)))
    monkeypatch.setattr(filedialog, "askdirectory", lambda **_: str(tmp_path))
    app = window(FakeBackend(settings=QUIET))
    app.main.add_files.invoke()
    app.main.add_folder.invoke()
    app.main.add_files.invoke()  # the same files again: never listed twice
    data = app.root.tk.call("list", str(tmp_path / "c d.odt"), str(first))
    app.inputs.dropped(SimpleNamespace(data=data))
    assert app.main.inputs.names() == ["a.pdf", "b.docx", f"{tmp_path.name}/", "c d.odt"]
    tree = app.main.inputs.tree
    tree.selection_set(tree.get_children()[0])
    app.main.remove.invoke()
    assert app.main.inputs.names()[0] == "b.docx"


def test_ac_06_the_picked_output_folder_is_remembered(
    window: Callable[..., TtkApp], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "Resultados"
    out.mkdir()
    monkeypatch.setattr(filedialog, "askdirectory", lambda **_: str(out))
    backend = MemoryBackend(QUIET)
    app = window(backend)
    assert app.main.output_mode.get() == "next_to"  # the default
    app.main.in_folder.invoke()
    assert app.presenter.output_folder == out
    assert backend.settings.last_output_folder == str(out)
    again = window(backend)
    assert again.presenter.settings.last_output_folder == str(out)  # the suggestion next time


# --- Before converting -----------------------------------------------------------------------


def test_ac_07_convert_first_shows_the_plan_and_writes_nothing(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    folder = copy_documents(tmp_path / "docs", "sample.docx", "sample.csv")
    (folder / "notes.md").write_text("# notes\n", encoding="utf-8")
    app = window(MemoryBackend(QUIET))
    to_review(app, folder)
    assert app.review.stats.figures() == [
        ("To Convert", "2"), ("Skipped", "1"), ("Already Exist", "0")
    ]  # fmt: skip
    assert app.review.files.names()[0] == "notes.md"  # what will not be converted, first
    assert not (tmp_path / "ClearMD_Output").exists()


@pytest.mark.parametrize(
    ("setting", "asked"), [("ask", True), ("overwrite", False), ("skip", False)]
)
def test_ac_08_existing_outputs_are_asked_about_only_with_ask(
    window: Callable[..., TtkApp], tmp_path: Path, setting: str, asked: bool
) -> None:
    plan = BatchPlan((planned("a.pdf", exists=True),), (), ())
    settings = replace_settings(QUIET, on_existing_output=setting)
    fake = FakeBackend(plan=plan, settings=settings)
    app = window(fake)
    to_review(app, tmp_path)
    assert bool(app.review.existing.winfo_ismapped()) is asked
    if asked:
        app.review.decision.set("overwrite")
    confirm(app)
    pump(app, until=lambda: converted(app))
    assert fake.run_calls[-1]["overwrite"](plan.conversions[0]) is (setting != "skip")
