# Plan — Feature 020: The summary as a PDF alone

> The **how**. Criteria: [`spec.md`](./spec.md). Decision: ADR-0031 (the PDF summary), amended.

- `backend/schemas/settings.py` — `summary_format` accepts `pdf`.
- `backend/api/__init__.py` — `run_batch(..., summary_markdown=False)`: the PDF alone; on failure the
  Markdown summary instead; an earlier Markdown summary is removed (a regular file, never a link).
- `frontend/presenter/intents/conversion.py` — the setting becomes `summary_pdf` and `summary_markdown`.
- `frontend/cli/` — `--summary-pdf-only`; `flow.summary_files` resolves flags and setting.
- `frontend/{ttk,pyside,flet}` — a third radio on step 1 and a third value in Settings.
- `i18n/{en,es}.toml` — `gui.main.summary_pdf_only`, `gui.settings.summary_pdf`, the new help.
