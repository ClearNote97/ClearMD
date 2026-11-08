# ttk/components — The pieces of the window

| Module | Role |
|---|---|
| `rail.py`, `rail_art.py` | The dark rail (state, events) and what it draws: Home, then the steps. |
| `file_list.py`, `file_list_keys.py` | The numbered file list and its keyboard and mouse. |
| `inputs_card.py`, `output_card.py` | The two halves of the Choose step. |
| `split_choice.py` | Split's choices in the output card: the cut, its number, what to keep (023). |
| `order_controls.py` | Merge's order: Move Up / Move Down on the selected row, and the hint (032). |
| `merge_choice.py` | Merge's choice in the output card: one Markdown or one PDF (026). |
| `tool_tile.py` | A large tile of the start screen: icon, title, what the tool does (023). |
| `flow_row.py` | A row of controls that wraps when too narrow (Review's answers, 028). |
| `scroll_area.py` | A frame that scrolls when taller than its room (Settings' rows; step 1's card, 032). |
| `drop_zone.py`, `action_bar.py`, `stats.py`, `surface.py` | Drop zone, bottom bar, figures, page ground. |
| `dialog.py` | The base of every dialog. |

Components import `visuals/` and `layout/`; never `views/`.
