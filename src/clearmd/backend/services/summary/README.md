# src/clearmd/backend/services/summary — `Resumen_ClearMD.md`

`writer.py` turns an `OutputRootReport` into the summary of its `ClearMD_Output` folder, in the user's
language: a name table (source → output, format, time), stopped, failed (with the technical detail), skipped,
kept and cancelled items, and the history of earlier batches carried over from the previous summary. File names
and error details come from untrusted documents, so they are escaped (table pipes, code spans, HTML).
