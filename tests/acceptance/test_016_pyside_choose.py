"""Feature 016 — Choose (AC-02); spec/features/016_*/spec.md.

The PySide6 window runs offscreen, on the presenter's fake backend.
"""

from collections.abc import Callable
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QFileDialog
from support.gui_fakes import FakeBackend, MemoryBackend
from support.pyside_acceptance import QUIET, drop, press, pump

from clearmd.frontend.presenter.icons import ICONS
from clearmd.frontend.pyside import PySideApp

Window = Callable[..., PySideApp]


def names(app: PySideApp) -> list[str]:
    return [row.name for row in app.main.inputs.rows()]


def test_ac_02_add_files_add_folder_drop_and_nothing_listed_twice(
    qt_window: Window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first, second = tmp_path / "a.pdf", tmp_path / "b.docx"
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        staticmethod(lambda *_a, **_k: ([str(first), str(second)], "")),
    )
    monkeypatch.setattr(
        QFileDialog, "getExistingDirectory", staticmethod(lambda *_a, **_k: str(tmp_path))
    )
    app = qt_window(FakeBackend(settings=QUIET))
    app.main.add_files.click()
    app.main.add_folder.click()
    app.main.add_files.click()  # the same files again: never listed twice
    drop(app, tmp_path / "c d.odt", first)
    assert names(app) == ["a.pdf", "b.docx", f"{tmp_path.name}/", "c d.odt"]


def test_ac_02_the_list_is_numbered_with_an_icon_on_every_row(
    qt_window: Window, tmp_path: Path
) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path / "b.docx", tmp_path / "n.xyz"])
    tree = app.main.inputs.tree
    assert tree.topLevelItemCount() == 3
    for index in range(3):
        item = tree.topLevelItem(index)
        assert item is not None and item.text(0) == str(index + 1) and not item.icon(1).isNull()
    assert tree.headerItem() is not None and tree.headerItem().text(0) == "#"
    icons = Path(__file__).resolve().parents[2] / "src/clearmd/frontend/assets/icons"
    assert all((icons / f"{name}.png").is_file() for name in ICONS)


def test_ac_02_remove_selected_clear_all_and_deselect_all(
    qt_window: Window, tmp_path: Path
) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path / "b.pdf", tmp_path / "c.pdf"])
    tree = app.main.inputs.tree
    first, second = tree.topLevelItem(0), tree.topLevelItem(1)
    assert first is not None and second is not None
    first.setSelected(True)
    assert first.checkState(0) == Qt.CheckState.Checked  # the boxes follow the selection
    second.setCheckState(0, Qt.CheckState.Checked)  # and a box joins its row to it
    assert len(tree.selectedItems()) == 2
    app.main.deselect.click()
    assert tree.selectedItems() == [] and first.checkState(0) == Qt.CheckState.Unchecked
    first.setSelected(True)
    app.main.remove.click()
    assert names(app) == ["b.pdf", "c.pdf"]
    tree.topLevelItem(0).setSelected(True)  # type: ignore[union-attr]
    tree.setFocus()
    press(app, Qt.Key.Key_Delete)  # the keyboard does the same
    assert names(app) == ["c.pdf"]
    app.main.clear.click()
    assert names(app) == [] and app.main.inputs.empty.text()  # the empty list says what to do


def test_ac_02_a_click_on_the_drop_zone_adds_files(
    qt_window: Window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    picked = tmp_path / "x.pdf"
    monkeypatch.setattr(
        QFileDialog, "getOpenFileNames", staticmethod(lambda *_a, **_k: ([str(picked)], ""))
    )
    app = qt_window(FakeBackend(settings=QUIET))
    QTest.mouseClick(app.main.drop_zone, Qt.MouseButton.LeftButton)
    assert names(app) == ["x.pdf"]


def test_ac_02_the_output_next_to_the_originals_or_in_a_folder_is_remembered(
    qt_window: Window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "Resultados"
    out.mkdir()
    monkeypatch.setattr(
        QFileDialog, "getExistingDirectory", staticmethod(lambda *_a, **_k: str(out))
    )
    backend = MemoryBackend(QUIET)
    app = qt_window(backend)
    assert app.main.output_mode() == "next_to" and app.main.next_to.isChecked()
    app.main.in_folder.click()
    assert app.presenter.output_folder == out and str(out) in app.main.output_label.text()
    assert backend.settings.last_output_folder == str(out)
    app.main.next_to.click()
    assert app.presenter.output_folder is None and app.main.next_to.isChecked()
    app.main.pick.click()  # "Choose folder…"
    assert app.presenter.output_folder == out and app.main.in_folder.isChecked()
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", staticmethod(lambda *_a, **_k: ""))
    app.main.next_to.click()
    app.main.in_folder.click()  # the dialog is cancelled: the choice stays as it was
    assert app.main.next_to.isChecked() and app.presenter.output_folder is None
    again = qt_window(backend)
    assert again.presenter.settings.last_output_folder == str(out)  # the suggestion next time


def test_ac_02_the_summary_format_and_the_images_choice(qt_window: Window) -> None:
    backend = MemoryBackend(QUIET)
    app = qt_window(backend)
    assert app.main.summary_md.isChecked() and app.main.images_omit.isChecked()
    app.main.summary_pdf.click()
    app.main.images_folder.click()
    assert backend.settings.summary_format == "markdown_pdf"
    assert backend.settings.images == "folder"
    again = qt_window(backend)  # remembered
    assert again.main.summary_pdf.isChecked() and again.main.images_folder.isChecked()
    app.main.summary_md.click()
    app.main.images_omit.click()
    assert backend.settings.summary_format == "markdown" and backend.settings.images == "omit"
    pump(app, seconds=0.02)


def test_ac_02_a_theme_change_keeps_the_selected_row(qt_window: Window, tmp_path: Path) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path / "b.pdf"])
    tree = app.main.inputs.tree
    second = tree.topLevelItem(1)
    assert second is not None
    second.setSelected(True)
    app.apply_theme("dark")
    assert app.shown.palette.mode == "dark"
    assert [item.text(0) for item in tree.selectedItems()] == ["2"]
