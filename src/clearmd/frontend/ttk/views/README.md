# ttk/views — One step per file

| Module | Role |
|---|---|
| `home.py` | Home, the start screen (`HomeView`): Convert, Split and Merge tiles (023, 026). |
| `choose.py` | Step 1, Choose (`ChooseView`): inputs card and output card. |
| `review.py` | Step 2, Review (`ReviewView`): the plan. |
| `convert.py` | Step 3, Convert (`ConvertView`): progress. |
| `results.py` | Step 4, Results (`ResultsView`). |
| `dialogs/` | The dialogs, one per file. |

Views import `components/`, `visuals/` and `layout/`; never the window.
