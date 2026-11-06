# ADR-0042: The flet GUI, delivered as a folder with its own window program

- **Status:** accepted
- **Date:** 2026-11-06
- **Refines:** ADR-0001 (one presenter, several toolkits), ADR-0038 (the PySide6 delivery),
  ADR-0040 (the installer).

## Context

flet is the third toolkit (feature 018), after ttk and PySide6. Unlike them, flet does not draw in
the Python process: it starts a separate **window program** (a Flutter app) and talks to it over a
local connection. On first use, flet downloads that program from GitHub into the user's home
folder (`~/.flet/client`). ClearMD is 100% local and never downloads anything on the user's machine.
flet 1.0 cannot receive files dragged onto its window from the system.

## Decision

- **flet 1.0.5** (`flet`, `flet-desktop`), pinned like every toolkit; 1.1.0 was one day old. Its
  young transitive releases are held back (`anyio`, `msgpack`, `oauthlib`), as the two-week rule asks.
- **The window program travels inside the app.** CI fetches it once
  (`packaging/fetch_flet_client.py`), checks it against a pinned SHA-256 (GitHub's own digest of
  the release file) and the flet spec copies it into `ClearMD-Flet/flet-client/flet/`, with its
  links and executable bits. The launcher sets `FLET_VIEW_PATH` to it, so flet neither downloads
  nor unpacks anything; CI checks that no `~/.flet` folder appears. Linux takes the "light" build
  for Ubuntu 22.04 (the build runner), which needs GTK 3 and libsecret from the system, as Qt needs
  its xcb libraries.
- **A folder** (`ClearMD-Flet/`, PyInstaller onedir), like the Qt app: released as
  `ClearMD-Flet-<v>-windows.zip`, inside the Linux archive, and as a fourth part of the installer.
  The other executables leave flet out; this one leaves tkinter and Qt out.
- **No drop on the window:** files come through Add files and Add folder (the UX contract asks for
  drag and drop "where the toolkit allows it"); the empty list says so.
- **The `flet` extra** (`pip install clearmd[flet]`, command `clearmd-flet`).

## Consequences

- **Gains:** the third toolkit, on the same presenter and layout; the owner can compare the three
  and choose; still nothing downloaded at run time.
- **Costs:** a third folder of about 120 MB; the window program is a binary we do not build (its
  checksum is pinned, its notices travel with it); on Linux the user needs GTK 3 (present on every
  common desktop).
