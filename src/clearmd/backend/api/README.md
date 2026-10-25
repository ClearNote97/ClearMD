# src/clearmd/backend/api — Facade (entry layer)

The template's endpoint layer, in-process: thin functions that every interface calls. They validate input,
call `use_cases/` and return `schemas/`. `composition.py` is the only place that builds the services.
