# docs/screenshots/005 — The first desktop app (ttkbootstrap)

Generated, never edited by hand (in the dev container, under a virtual display):

```bash
uv run python tests/gui/screenshots.py --out docs/screenshots/005   # every screen: light/dark, EN/ES
uv run python tests/gui/flow.py --out docs/screenshots/005 --language es   # a real batch, animated
```

| File | What |
|---|---|
| `0-welcome-*` | The welcome on first run |
| `1-choose-*` | Step 1: what to convert, where the results go |
| `2-review-*` | Step 2: the plan, before anything is written |
| `3-convert-*` | Step 3: the progress (a batch held mid-way) |
| `4-results-*` | Step 4: the figures and what needs attention |
| `5-help-*`, `6-settings-*` | The help and the settings |
| `flow-*.gif` | A real batch (the test documents) through the real backend |

The screens are filled by a fake backend; `flow-*.gif` converts for real. Without a window manager, the
dialogs have no title bar here.
