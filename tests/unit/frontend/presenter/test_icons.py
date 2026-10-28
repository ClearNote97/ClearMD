"""Which icon each row gets (ADR-0027): by format, plus folders, Markdown and anything else."""

from pathlib import Path

import pytest

from clearmd.backend.schemas.formats import EXTENSIONS
from clearmd.frontend.presenter.icons import ICONS, icon_for


@pytest.mark.parametrize(
    ("name", "icon"),
    [
        ("Informe.pdf", "pdf"),
        ("Contrato.DOCX", "docx"),
        ("pagina.htm", "html"),
        ("libro.epub", "epub"),
        ("notas.md", "markdown"),
        ("notas.markdown", "markdown"),
        ("fotos.zip", "unknown"),
        ("sin_extension", "unknown"),
    ],
)
def test_a_file_gets_the_icon_of_its_extension(name: str, icon: str) -> None:
    assert icon_for(Path("/docs") / name, is_folder=False) == icon


def test_a_folder_gets_the_folder_icon_whatever_its_name() -> None:
    assert icon_for(Path("/docs/tesis.pdf"), is_folder=True) == "folder"


def test_every_supported_format_has_its_own_icon() -> None:
    assert {icon_for(Path(f"a{ext}"), is_folder=False) for ext in EXTENSIONS} <= ICONS
    assert "unknown" not in {icon_for(Path(f"a{ext}"), is_folder=False) for ext in EXTENSIONS}
