# tests/acceptance — Acceptance tests (per feature)

They verify that what was built meets the **acceptance criteria** of each feature's `spec.md`.
One file per feature (`test_001_batch_conversion.py` ↔ `spec/features/001_batch-conversion-core-cli/`),
one test per criterion, named after its id (`AC-01` …). They are the proof that the code honors the spec.
