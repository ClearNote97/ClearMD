# Tasks — Refactor R01: Modular layout and file size

Each phase ends green (G2: full suite, executables, archive listing) and is tagged `refactor-pN`.
The owner first asked for reviews after P1, P8, P11 and P12, then (2026-11-05) for the whole
refactor without stops: doubts go back to the board, and to the owner only if it cannot solve them.

- [x] **P0 — Baseline** (local only): test ids, suite, golden manifest, screenshots, sizes, build.
- [x] **P1 — Safety net:** the palette rule; PySide6 out of the executables; this spec and ADR-0039
  (proposed); the size test with its ratchets; the architecture rules; the entry points test; the
  golden tests and characterisation tests. **Review.**
- [ ] **P2 — `qt` → `pyside`.**
- [ ] **P3 — `design/` and `launch.py`.**
- [ ] **P4 — `presenter/chrome/`.**
- [ ] **P5 — The presenter split.**
- [ ] **P6 — The CLI.**
- [ ] **P7 — ttk in the layout.**
- [ ] **P8 — pyside in the layout.** **Review.**
- [ ] **P9 — The PDF converter.**
- [ ] **P10 — The rest of the backend.**
- [ ] **P11 — Close the source:** ratchets empty; ADR-0039 accepted; READMEs. **Review.**
- [ ] **P12 — The tests.** **Review.**
