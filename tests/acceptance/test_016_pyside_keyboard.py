"""Feature 016 — Everything works with the keyboard (AC-02, AC-04); spec/features/016_*/spec.md.

The PySide6 window runs offscreen, on the presenter's fake backend.
"""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QItemSelectionModel, Qt
from PySide6.QtWidgets import QApplication, QWidget
from support.gui_fakes import FakeBackend
from support.pyside_acceptance import QUIET, press, pump

from clearmd.frontend.pyside import PySideApp

Window = Callable[..., PySideApp]


def test_ac_04_the_tab_key_reaches_every_control_of_the_page(
    qt_window: Window, tmp_path: Path
) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    app.presenter.add_paths([tmp_path])
    pump(app, seconds=0.1)
    app.main.add_files.setFocus()
    chain: list[QWidget] = []
    for _ in range(40):
        focused = QApplication.focusWidget()
        assert focused is not None
        chain.append(focused)
        app.window.focusNextPrevChild(True)
        if QApplication.focusWidget() is app.main.add_files:
            break
    assert {app.main.add_folder, app.main.inputs.tree, app.actions.primary} <= set(chain)
    assert app.main.next_to in chain and app.main.remove in chain


def test_ac_02_space_checks_a_file_ctrl_a_checks_all_and_delete_removes(
    qt_window: Window, tmp_path: Path
) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path / "b.pdf", tmp_path / "c.pdf"])
    tree = app.main.inputs.tree
    tree.setFocus()
    first = tree.topLevelItem(0)
    assert first is not None
    tree.setCurrentItem(first, 0, QItemSelectionModel.SelectionFlag.NoUpdate)
    assert tree.selectedItems() == []  # on a file, not checked yet
    press(app, Qt.Key.Key_Space)  # the current file's box
    assert [item.text(0) for item in tree.selectedItems()] == ["1"]
    press(app, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)  # all of them
    assert len(tree.selectedItems()) == 3
    states = [tree.topLevelItem(i).checkState(0) for i in range(3)]  # type: ignore[union-attr]
    assert states == [Qt.CheckState.Checked] * 3
    press(app, Qt.Key.Key_Delete)
    assert app.main.inputs.rows() == ()
