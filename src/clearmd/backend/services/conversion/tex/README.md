# src/clearmd/backend/services/conversion/tex — The LaTeX converter (feature 002)

ClearMD's own converter on `pylatexenc` (ADR-0006), imported only inside the worker process. Its rules —
following includes only inside the document folder, expanding the author's macros with limits, and reporting
what it could not do as conversion notes — are in ADR-0022 and `spec/features/002_tex-converter/`.
