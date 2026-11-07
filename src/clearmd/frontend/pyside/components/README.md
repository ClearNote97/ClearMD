# pyside/components — The pieces of the window

| Module | Role |
|---|---|
| `primitives.py` | A named label, a button, a card, a radio button, `restyle`. |
| `rail.py`, `rail_art.py` | The dark rail (Home, the steps; state, events) and what it draws. |
| `tile.py`, `tile_art.py` | A start tile (feature 023) and its icons: the document, the scissors. |
| `file_list.py` | The numbered file list. |
| `output_card.py`, `split_choice.py` | Step 1's results card; How to Split, in place of the images for Split. |
| `drop_zone.py`, `action_bar.py`, `stats.py`, `surface.py` | Drop zone, bottom bar, figures, page ground. |
| `dialog.py` | The base of every dialog. |

Components import `visuals/` and `layout/`; never `views/`.
