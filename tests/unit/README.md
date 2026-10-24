# tests/unit — Unit tests

One file per module of `src/clearmd/`. The core is tested without GUI, and without the real disk when
possible (pure functions; `tmp_path` for the file system).
