# tests/unit — Unit tests

A mirror of `src/clearmd/`: `tests/unit/backend/use_cases/test_planning.py` tests
`clearmd/backend/use_cases/planning.py`. The backend is tested without any GUI, and without the real disk when
possible (pure functions; `tmp_path` for the file system).
