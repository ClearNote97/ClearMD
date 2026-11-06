# src/clearmd/frontend — User interfaces

Every interface talks only to `backend/api` and `backend/schemas` (ADR-0014) and follows
`spec/contracts/ux.md`.

| Folder | Role |
|---|---|
| `cli/` | Command-line interface (feature 001). |
| `presenter/` | Interaction logic shared by the GUIs, the template's `state/` role (feature 005). |
| `ttk/`, `pyside/` | One GUI each, in its phase, with the template's `app/`, `views/`, `components/`, `layout/`. |
| `flet/` | The flet GUI (feature 018): the same layout, drawn by flet; no drop on the window. |
