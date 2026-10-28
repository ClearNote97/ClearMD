# ADR-0027: ClearMD's visual identity

- **Status:** accepted
- **Date:** 2026-10-28
- **Refines:** ADR-0026 (the presenter and the ttk GUI), `spec/contracts/ux.md` §5 (look).

## Context

The first ttk window (005, T04) worked but looked like a default Tk form: grey square buttons, no brand, no
sense of where the user is in the flow. ClearMD is for people who have never opened a terminal; the window is
the product. The author reviewed a visual proposal (a design canvas with the main screen in two palettes,
light and dark, the file icons and several logo concepts) and chose the direction below.

## Decision

### Layout: the "Contemporáneo" style

The author's own template family ("Contemporáneo" of ClearNote BI Visual Forge) adapted to a desktop window:

- **A dark rail on the left**: the logo and the name, the four steps of the flow — **1 Choose · 2 Review ·
  3 Convert · 4 Results** — with the current one highlighted, and Settings, Help and "100 % local" at the
  bottom. The step replaces the plain state label: the user sees where they are.
- **A light working area on the right**: a header (step counter, title, one-line explanation) over white
  cards with rounded corners, and a soft organic shape in the background.
- One primary action per screen, at the bottom right.

### Palette: teal (light and dark)

| Role | Light | Dark |
|---|---|---|
| Rail (ink) | `#1B2733` | `#0F161C` |
| Background | `#F3F5F7` | `#18212A` |
| Card | `#FFFFFF` | `#202B36` |
| Text / secondary text | `#1B2733` / `#5B6672` | `#E6EBEF` / `#A3AEB8` |
| Border | `#DCE2E7` | `#2E3B47` |
| Accent (primary action, current step) | `#0F766E` | `#2DD4BF` |
| Light accent (the "Clear" tone) | `#0D9488` | `#99F6E4` |
| Background shape | `#D7EEEA` | `#1E3A3A` |
| Warning (skipped, problems) | `#B45309` | `#F59E0B` |

Every text pair passes WCAG AA (measured: 5.0:1 the lowest). The alternative palette (petroleum blue
`#2F5D7C`) was shown and not chosen.

### Logo: "the C embraces the M"

- A **C** drawn as a three-quarter arc in the light accent, lower than the M and apart from it; an **M** whose
  right leg goes on down and ends in an **arrow**. It reads "Clear receives, Markdown delivers".
- Versions: colour on light, colour on dark, ink monochrome, inverted monochrome, and an **app icon** (the
  mark in white and the light tone on a teal rounded square) at 16, 32, 48, 64, 128 and 256 px.
- Drawn by ClearMD's own code from one geometry (strokes only, no font), which writes both the SVG files and
  the PNG files: no design tool, no third-party artwork.
- The name is written **Clear·MD** in the window and the README, the middle dot in the light accent — the same
  tone as the logo's C. The product name stays "ClearMD" everywhere else (commands, packages, paths).

### File icons

- A page with a folded corner in the format's colour and its initial(s) in white, centred: **PDF**, **W**
  (Word), **X** (Excel), **P** (PowerPoint), **O** (OpenDocument), **TeX**, **`</>`** (HTML), **CSV**, **E**
  (EPUB), **NB** (notebook), **T** (text), **M↓** (Markdown, skipped) and **?** (any other file); a yellow
  folder for folders. Every colour passes 4.5:1 under white text.
- ClearMD's own drawings, not an icon theme's: no licence question in a public repository.
- Generated as PNG files (letters rendered at build time with a bundled-with-the-container font, so the app
  needs no font for them), shipped in `frontend/assets/`, shared by the three GUIs.
- The list of inputs reads **# · icon and name · folder**; the plan and the result use the same icons.

### Type

The system's font (Segoe UI on Windows), never below 14 px (ADR-0026). No font is shipped.

### How Tk draws it (ttk only)

- Two ttkbootstrap themes of ClearMD's own, `clearmd-light` and `clearmd-dark`, carry the palette (buttons,
  radio buttons, progress bar, lists take the accent by themselves).
- Rounded buttons and cards are ttk **image elements**: Pillow (already required by ttkbootstrap) draws the
  rounded shapes, stretched without distortion (nine-slice). They stay real ttk widgets: keyboard, focus
  (a visible focus ring is part of the image), disabled state.
- The rail and the background shape are drawn on a Tk canvas.
- The window icon is the app icon.

### Assets

`src/clearmd/frontend/assets/` holds the logo (SVG and PNG) and the file icons (PNG). A development script
(`tests/gui/make_assets.py`, run in the container) regenerates them; a test checks the committed files match
what the script draws, so they never drift.

## Consequences

- **Gains:** a recognisable product; the user always knows the step they are on; PySide6 (007) and flet (008)
  reuse the palette, the logo and the icons as they are.
- **Costs:** the T04 window is redone on this design (its logic stays); image elements must be rebuilt when
  the theme changes; screenshots must be regenerated.

## Alternatives considered

- **ttkbootstrap's stock themes:** no work, no identity (the T04 look). Rejected by the author.
- **Material Icon Theme's icons:** MIT, but some icons come from third parties under other licences; not worth
  the doubt in a public repository.
- **Logos with letters set in a font** (CN/MD blocks, a stamp): too busy at 16 px (the author's verdict); the
  chosen mark is strokes only.
- **The petroleum palette** of the author's template: sober but generic; the teal stands out and evokes
  clarity.
