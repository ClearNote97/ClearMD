# src/ — Implementation (core + adapters)

The `clearmd` package (`src/` layout, ADR-0007). Dependencies point **toward the core**, never the other way
around (ADR-0001). Each subpackage documents its role in the docstring of its `__init__.py`.

| Folder | Role |
|---|---|
| `clearmd/core/` | Domain: ports (`DocumentConverter`, `FormatDetector`), models and use cases. Imports no GUI and no conversion library. |
| `clearmd/converters/` | Conversion adapters: the markitdown wrapper and the own converters (.tex, .odt, HTML article mode). |
| `clearmd/presenter/` | Interaction logic shared by every GUI (MVP pattern). |
| `clearmd/cli/` | Command-line adapter: the first interface, and the one acceptance tests drive. |

Feature 001 adds `i18n/`, `detection/`, `config/` and `composition.py` (see its
[plan](../spec/features/001_batch-conversion-core-cli/plan.md)). GUIs (`ttk`, `qt`, `flet`) arrive as
subpackages in their phase (see `spec/roadmap.md`).
