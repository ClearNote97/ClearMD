# src/clearmd/backend/services/split — Split's page work (feature 023, ADR-0044)

- `pdf_pages.py` — a PDF's page count, and a new PDF with a range of its pages copied whole by PDFium.
  It runs in the worker process (`worker/pages.py`), never in the interface.
