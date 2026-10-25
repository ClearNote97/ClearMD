# src/clearmd/backend/services/detection — Format detection

`extension.py` maps the file extension to a format without reading the file; it runs in the CLI process. The
content detector (magika) runs inside the worker and joins in T10, chained after this one.
