# src/clearmd/backend/services/conversion — Converters

`markitdown_adapter.py` wraps markitdown (ADR-0004) and maps its exceptions to `ErrorCode`s; `registry.py` picks
the converter of each format. **Imported only inside the worker process** (ADR-0015, AC-19): the CLI process
never loads markitdown. Own converters (`.tex`, `.odt`, HTML article mode) join the registry in features
002–004.
