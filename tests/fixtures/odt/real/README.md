# tests/fixtures/odt/real — Files made by LibreOffice

`report.odt` is `report.fodt` saved by **LibreOffice 7.4** (`make_real.sh`): its styles, manifest, embedded
picture and the MathML of its formulas are LibreOffice's own, not ClearMD's generator. It is committed because
LibreOffice is not part of the dev container (it was installed only while building feature 003). Unlike the
generated fixtures one folder up, it is not byte-reproducible (LibreOffice stamps dates).
