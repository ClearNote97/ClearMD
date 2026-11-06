# flet/components — The pieces of the window

| Module | Role |
|---|---|
| `primitives.py` | A text of a kind, a button, a card, a gap, `Choice` (radio buttons), `Wording` (catalog texts). |
| `rail.py`, `rail_art.py` | The dark rail (state, events) and what it draws (badges, its buttons' look). |
| `file_list.py` | The numbered file list, with boxes where its selection does something. |
| `inputs_card.py`, `output_card.py` | Choose's two halves: what to convert, where it goes. |
| `action_bar.py`, `stats.py`, `surface.py` | Bottom bar, figures, the working area and its header. |
| `dialog.py` | The base of every dialog. |

No drop zone: flet 1.0 cannot receive files dropped from the system (feature 018).
Components import `visuals/` and `layout/`; never `views/`.
