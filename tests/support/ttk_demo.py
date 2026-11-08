"""The demo the ttk screenshots show (tests/gui/screenshots.py): real files and folders under a
temporary home, the plan a fake backend returns, and its variants (a failure, a large PDF)."""

import tempfile
from pathlib import Path

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus, PlanWarning, SkippedItem
from support.gui_fakes import planned

# Real files and folders (a folder must exist to be shown as one), under a temporary home.
DEMO = Path(tempfile.gettempdir()) / "Usuarios" / "ana"
DOCUMENTS, DOWNLOADS = DEMO / "Documentos", DEMO / "Descargas"
INPUTS = [
    DOCUMENTS / "Informe anual 2026.pdf",
    DOCUMENTS / "Tesis",
    DOWNLOADS / "Contrato de arriendo.docx",
    DOCUMENTS / "Finanzas" / "Ventas 2026.xlsx",
    DOWNLOADS / "Notas de clase.odt",
    DOCUMENTS / "Tesis" / "Artículo.tex",
]
PLAN = BatchPlan(
    (
        planned("Informe anual 2026.pdf", folder=DOCUMENTS),
        planned("Capítulo 1.docx", folder=DOCUMENTS / "Tesis"),
        planned("Artículo.tex", folder=DOCUMENTS / "Tesis", exists=True),
        planned("Contrato de arriendo.docx", folder=DOWNLOADS),
        planned("Ventas 2026.xlsx", folder=DOCUMENTS / "Finanzas"),
        planned("Notas de clase.odt", folder=DOWNLOADS),
    ),
    (
        SkippedItem(DOCUMENTS / "Tesis" / "borrador.md", SkipReason.ALREADY_MARKDOWN),
        SkippedItem(DOCUMENTS / "Tesis" / "figuras.zip", SkipReason.ZIP_ARCHIVE),
    ),
    (),
)
FAILED = {"Contrato de arriendo.docx": OutcomeStatus.FAILED}
# A PDF too slow for the time limit: Review offers to split it (feature 025).
OFFER = BatchPlan(
    PLAN.conversions, PLAN.skipped, (), (PlanWarning(PLAN.conversions[0], 2400, 600),)
)


def demo_files() -> None:
    for path in INPUTS:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix:
            path.write_bytes(b"")
        else:
            path.mkdir(exist_ok=True)
