# ttk/components — The pieces of the window

| Module | Role |
|---|---|
| `rail.py`, `rail_art.py` | The dark rail (state, events) and what it draws. |
| `file_list.py`, `file_list_keys.py` | The numbered file list and its keyboard and mouse. |
| `inputs_card.py`, `output_card.py` | The two halves of the Choose step. |
| `drop_zone.py`, `action_bar.py`, `stats.py`, `surface.py` | Drop zone, bottom bar, figures, page ground. |
| `dialog.py` | The base of every dialog. |

Components import `visuals/` and `layout/`; never `views/`.
