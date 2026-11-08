# pyside/components — The pieces of the window

| Module | Role |
|---|---|
| `primitives.py` | A named label, a button, a card, a radio button, `restyle`. |
| `rail.py`, `rail_art.py` | The dark rail (Home, the steps; state, events) and what it draws. |
| `tile.py`, `tile_art.py` | A start tile (feature 023) and its icons, painted from `design/tool_art.py` (032). |
| `file_list.py` | The numbered file list. |
| `order_column.py` | Merge's ▲ ▼ on each row of step 1's list (032). |
| `fold_row.py` | A row of choices that wraps into aligned columns when it does not fit. |
| `output_card.py`, `split_choice.py`, `merge_choice.py` | Step 1's results card; How to Split or How to Merge in place of the images. |
| `drop_zone.py`, `action_bar.py`, `stats.py`, `surface.py` | Drop zone, bottom bar, figures, page ground. |
| `dialog.py` | The base of every dialog. |

Components import `visuals/` and `layout/`; never `views/`.
