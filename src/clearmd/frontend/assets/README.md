# assets/

ClearMD's logo and file icons (ADR-0027), shared by every GUI. Generated, never edited by hand:

```bash
uv run python tests/gui/make_assets.py   # in the dev container
```

`tests/unit/frontend/test_assets.py` fails if these files and the script disagree.

| Folder | What |
|---|---|
| `logo/` | The mark (C·M↓) for light and dark backgrounds and in ink, as SVG and PNG; the app icon (`clearmd-app-*.png`) |
| `qt/` | The Qt window's check mark and list arrow, for each theme (SVG, written by hand: four tiny paths) |
| `icons/` | One icon per format, plus `folder`, `markdown` and `unknown`; 28 px and `@2x` |
