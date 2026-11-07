# flet/components — The pieces of the window

| Module | Role |
|---|---|
| `primitives.py` | A text of a kind, a button, a card, a gap, `Choice` (radio buttons), `Wording` (catalog texts). |
| `rail.py`, `rail_art.py` | The dark rail (state, events) and what it draws (badges, its buttons' look). |
| `rail_home.py` | Home on the rail, above the steps (feature 023). |
| `file_list.py` | The numbered file list, with boxes where its selection does something. |
| `inputs_card.py`, `output_card.py` | Choose's two halves: what to convert, where it goes. |
| `start_panel.py` | Choose before anything is listed: two large tiles, Add files and Add folder (feature 021); its `Tile` is Home's too. |
| `split_block.py` | How to Split on step 1 of Split: the cut, its numbers, what to keep (feature 023). |
| `action_bar.py`, `stats.py`, `surface.py` | Bottom bar, figures, the working area and its header. |
| `dialog.py` | The base of every dialog. |

No drop zone: flet 1.0 cannot receive files dropped from the system (feature 018); the empty list
is the two start tiles instead (feature 021).
Components import `visuals/` and `layout/`; never `views/`.
