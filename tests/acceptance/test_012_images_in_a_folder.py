"""Feature 012 — one test per acceptance criterion (spec/features/012_*/spec.md): real batches
through the command line."""

import io
import shutil
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from PIL import Image
from support import DOCUMENTS_DIR, ODT_DIR
from support.gui_close import shut
from support.gui_fakes import FakeBackend

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.cli import main
from clearmd.frontend.ttk import TtkApp

ROOT = Path(__file__).resolve().parents[2]


def picture(colour: str = "red") -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (80, 50), colour).save(buffer, "PNG")
    return buffer.getvalue()


def batch(workdir: Path) -> Path:
    import pptx
    from pptx.util import Inches

    docs = workdir / "docs"
    docs.mkdir()
    image = workdir / "red.png"
    image.write_bytes(picture())
    deck = pptx.Presentation()
    deck.slides.add_slide(deck.slide_layouts[6]).shapes.add_picture(
        str(image), Inches(1), Inches(1)
    )
    deck.save(str(docs / "deck.pptx"))
    Image.new("RGB", (300, 200), "blue").save(docs / "scan.pdf", "PDF")
    shutil.copyfile(ODT_DIR / "images.odt", docs / "report.odt")
    shutil.copyfile(DOCUMENTS_DIR / "sample.txt", docs / "notes.txt")
    return docs


def output(workdir: Path) -> Path:
    return workdir / "ClearMD_Output" / "OutputMD" / "docs"


def test_ac_01_pictures_go_to_a_folder_next_to_the_markdown(workdir: Path) -> None:
    docs = batch(workdir)
    assert main([str(docs), "--quiet", "--images"]) == 0
    out = output(workdir)
    for name in ("deck", "scan", "report"):
        markdown = (out / f"{name}.md").read_text(encoding="utf-8")
        assert f"]({name}_images/image-001.png)" in markdown, name
        assert (out / f"{name}_images" / "image-001.png").is_file(), name
    assert not (out / "notes_images").exists()  # no picture, no folder


def test_ac_01_the_suffix_follows_the_language(workdir: Path) -> None:
    docs = batch(workdir)
    main([str(docs), "--quiet", "--images", "--lang", "es"])
    assert (output(workdir) / "scan_imagenes" / "image-001.png").is_file()


def test_ac_02_by_default_no_picture_is_written(workdir: Path) -> None:
    docs = batch(workdir)
    main([str(docs), "--quiet"])
    out = output(workdir)
    assert not any(path.name.endswith("_images") for path in out.iterdir())
    assert "*Image: Mapa de la región*" in (out / "report.md").read_text(encoding="utf-8")


def test_ac_03_a_picture_used_again_is_kept_once(workdir: Path) -> None:
    docs = batch(workdir)
    main([str(docs), "--quiet", "--images"])
    assert len(list((output(workdir) / "report_images").iterdir())) == 1  # used three times


def test_ac_04_earlier_pictures_are_replaced_and_a_link_is_never_followed(workdir: Path) -> None:
    docs = batch(workdir)
    main([str(docs), "--quiet", "--images"])
    folder = output(workdir) / "scan_images"
    (folder / "image-005.png").write_bytes(picture("green"))
    main([str(docs), "--quiet", "--images", "--overwrite"])
    assert sorted(path.name for path in folder.iterdir()) == ["image-001.png"]
    elsewhere = workdir / "elsewhere"
    elsewhere.mkdir()
    shutil.rmtree(folder)
    folder.symlink_to(elsewhere)
    main([str(docs), "--quiet", "--images", "--overwrite"])
    assert list(elsewhere.iterdir()) == []


@pytest.fixture
def app(display: str) -> Iterator[TtkApp]:
    window = TtkApp(FakeBackend(settings=Settings(show_welcome=False)))
    window.start()
    yield window
    shut(window)


def test_ac_05_the_choice_on_step_1_in_settings_and_the_cli(app: TtkApp) -> None:
    assert app.main.images.get() == "omit"
    folder_choice = next(b for b in app.main.summary_buttons if str(b.cget("value")) == "folder")
    folder_choice.invoke()
    assert app.presenter.settings.images == "folder"
    app.show_settings()
    deadline = time.monotonic() + 2
    while app.dialog is None and time.monotonic() < deadline:
        app.root.update()
    assert app.dialog is not None and "images" in getattr(app.dialog, "values", {})
    app.dialog.close()
    shots = ROOT / "docs" / "screenshots" / "012"
    for theme in ("light", "dark"):
        for language in ("en", "es"):
            assert (shots / f"1-choose-{theme}-{language}.png").is_file()
