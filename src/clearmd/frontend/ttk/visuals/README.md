# ttk/visuals — The toolkit's styles and drawings

| Module | Role |
|---|---|
| `style_names.py` | The names of the ttk styles ClearMD adds (`PRIMARY`, `CARD`, `MUTED`...). |
| `themes.py` | `clearmd-light` and `clearmd-dark`, registered with ttkbootstrap. |
| `look.py` | `Look`: installs the styles once per theme and keeps their images. |
| `styles.py` | The styles themselves: buttons, cards, labels, the list and its heading. |
| `buttons.py` | The rounded button element. |
| `shapes.py` | Pillow shapes: rounded rectangles, dashes, the background shape, circles. |
| `marks.py` | Pillow marks: file icons, logo, checkbox, a row's number, a heading's cell. |
| `tool_marks.py` | Pillow marks of the tools: document (Convert), scissors (Split), merge (Merge), house (Home). |

Imports only `frontend.design` and the libraries; never `components/` or `views/`.
