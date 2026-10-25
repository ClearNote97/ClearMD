from pathlib import Path

from clearmd.backend.use_cases.paths import output_root_for, target_for


def test_a_file_writes_next_to_itself() -> None:
    assert output_root_for(Path("/d/report.pdf"), is_dir=False) == Path("/d/ClearMD_Output")


def test_an_explicit_output_folder_replaces_the_parent() -> None:
    root = output_root_for(Path("/d/report.pdf"), is_dir=False, override=Path("/x"))
    assert root == Path("/x/ClearMD_Output")


def test_target_keeps_the_full_stem_and_goes_into_output() -> None:
    root = Path("/d/ClearMD_Output")
    assert (
        target_for(Path("/d/report.v2.final.pdf"), root) == root / "Output" / "report.v2.final.md"
    )


def test_target_of_a_file_without_extension() -> None:
    root = Path("/d/ClearMD_Output")
    assert target_for(Path("/d/scan"), root) == root / "Output" / "scan.md"


def test_unicode_names_are_preserved() -> None:
    root = Path("/d/ClearMD_Output")
    assert target_for(Path("/d/informe_año_ñ.docx"), root).name == "informe_año_ñ.md"
